"""

A helper plugin for downloading executables from the internet to help other
Plugins which might rely on external executables .

@NOTE remote urls may be tarballs/zips

@NOTE it goes without saying that downloading executables comes with an inherit
risk.  The request validates any certs, but it is up to you to make sure that
no config is in place which downloads dangerous bins.

The idea here is that you can tell your system to put bins from a list of
urls into a path, and have that path included in PATH in your python environment.
If you want, use a common system path like '/usr/local/bin' or use a temporary
or local path if you want to isolate versions for your test suite.

There are two ways you can use this:

1. put a list of bins into the plugin config, and it will download when it is
constructed.  This de-couples acquiring bins from plugins that may use them, and
does all of the downloading up front before all fixtures are created.
If another fixture needs a bin in its own constructor, just make sure that this
fixture is created first.

2. any other code with access to the environment can access the binhelper plugin
and provide details to the `get_bin` method.  This couples the plugins, and
means that you will have to ensure that this plugin is available and handle
dependencies yourself.

"""
from typing import Dict
import shutil
import os
import logging
import requests
import tarfile
import zipfile
import re
import stat
import platform

from configerus.loaded import LOADED_KEY_ROOT
from configerus.contrib.jsonschema.validate import PLUGIN_ID_VALIDATE_JSONSCHEMA_SCHEMA_CONFIG_LABEL
from configerus.validator import ValidationError

from mirantis.testing.metta.plugin import METTAPlugin
from mirantis.testing.metta.environment import Environment

logger = logging.getLogger('metta.common.utility:binhelper')

METTA_PLUGIN_ID_UTILITY_BINHELPER = 'bin-helper'
""" utility plugin_id for the bin-helper plugin """

BINHELPER_UTILITY_CONFIG_LABEL = 'binhelper'
""" Config label used by default to load binhelper configuration """

BINHELPER_UTILITY_CONFIG_BASE_LOCALPATH = 'path.local'
""" config base for what the local bin path should be """
BINHELPER_UTILITY_CONFIG_BASE_ADDTOPATH = 'path.add_to_path'
""" config base for whether or not we need to modify the env PATH and add the path """
BINHELPER_UTILITY_CONFIG_BASE_PLATFORMS = 'platforms'
""" config base for list of platform bins to load on construction """

BINHELPER_UTILITY_CONFIG_BASE_BIN_URL = 'url'
""" config base inside bin for bin url for downloading """
BINHELPER_UTILITY_CONFIG_BASE_BIN_VERSION = 'version'
""" config base inside bin for bin version """
BINHELPER_UTILITY_CONFIG_BASE_BIN_COPYPATHS = 'copy'
""" config base inside bin for a map of bins name->path-inpackage """

BINHELPER_CONFIG_JSONSCHEMA = {
    'type': 'object',
    'path': {
        'type': 'object',
        'properties': {
            'local': {'type': 'string'},
            'add_to_environ': {'type': 'bool'}
        },
        'required': ['path']
    },
    'platforms': {
        '$ref': '#/definitions/platform'
    },
    'definitions': {
        'bin': {
            'type': 'object',
            'properties': {
                'url': {'type': 'string'},
                'version': {'type': 'string'},
                'copy': {'type': 'object'}
            },
            'required': ['url']
        },
        'platform': {
            '$ref': '#/definitions/bin'
        },
    },
    'required': ['path', 'platforms']
}
""" JSONSCHEMA for the binhelper config """
BINHELPER_CONFIG_VALIDATE_TARGET = {
    PLUGIN_ID_VALIDATE_JSONSCHEMA_SCHEMA_CONFIG_LABEL: BINHELPER_CONFIG_JSONSCHEMA}
""" configerus validate target for binhelper config """


class DownloadableExecutableUtility(METTAPlugin):
    """ A helper to help you handle those pesky executables for tools which you need to download """

    def __init__(self, environment: Environment, instance_id: str,
                 label: str = BINHELPER_UTILITY_CONFIG_LABEL, base: str = LOADED_KEY_ROOT):
        """

        Parameters:
        -----------

        """
        METTAPlugin.__init__(self, environment, instance_id)

        loaded = self.environment.config.load(label)
        try:
            loaded.get(
                base,
                validator=BINHELPER_CONFIG_VALIDATE_TARGET)
        except KeyError as e:
            raise ValueError("Bin-Helper configuration is missing") from e
        except ValidationError as e:
            raise ValueError(
                "Bin-Helper received invalid configuration: {}".format(e)) from e

        self.local_path = loaded.get(
            [base, BINHELPER_UTILITY_CONFIG_BASE_LOCALPATH])

        add_to_path = loaded.get([base,
                                  BINHELPER_UTILITY_CONFIG_BASE_ADDTOPATH])
        if add_to_path:
            os.environ["PATH"] += os.pathsep + \
                os.path.realpath(self.local_path)

        platforms = loaded.get([base,
                                BINHELPER_UTILITY_CONFIG_BASE_PLATFORMS])
        current_platform = '{}-{}'.format(platform.system(),
                                          platform.machine())

        if current_platform not in platforms:
            logger.warn("BinHelper doesn't have configuration for your platform '{}', so it won't download any bins.".format(
                current_platform))
            return

        bins = platforms[current_platform]
        for bin_id in list(bins.keys()):
            url = loaded.get([base,
                              BINHELPER_UTILITY_CONFIG_BASE_PLATFORMS,
                              current_platform,
                              bin_id,
                              BINHELPER_UTILITY_CONFIG_BASE_BIN_URL])
            version = loaded.get([base,
                                  BINHELPER_UTILITY_CONFIG_BASE_PLATFORMS,
                                  current_platform,
                                  bin_id,
                                  BINHELPER_UTILITY_CONFIG_BASE_BIN_VERSION])
            copypaths = loaded.get([base,
                                    BINHELPER_UTILITY_CONFIG_BASE_PLATFORMS,
                                    current_platform,
                                    bin_id,
                                    BINHELPER_UTILITY_CONFIG_BASE_BIN_COPYPATHS])
            self.get_bin(
                name=bin_id,
                url=url,
                version=version,
                copypaths=copypaths)

    def get_bin(self, name: str, url: str, version: str,
                copypaths: Dict[str, str] = None):
        """ get a remote bin package, and put any bin contents into a bin path

        Make sure that we have the bin in scope; download it if we don't

        """
        path = shutil.which(name, os.X_OK)

        if path is None:
            logger.info(
                "bin-helper can't find {}. Downloading it from {}".format(name, url))

            # First get the url
            r = requests.get(url, allow_redirects=True)
            r.raise_for_status()

            # try to decide on a name for the download
            file_name = None
            content_disposition = r.headers.get('content-disposition')
            if content_disposition is not None:
                file_name_matches = re.findall(
                    'filename=(.+)', content_disposition)
                if file_name_matches:
                    file_name = file_name_matches[0]
            if file_name is None:
                # @NOTE this may not be a reliable way of getting a name from a url
                file_name = os.path.basename(url)

            # write the file into our local path
            local_file = os.path.join(self.local_path, file_name)
            with open(local_file, 'wb') as f:
                f.write(r.content)

            # downloaded url is a tarfile.  Copy only the files out of the tarfile
            # that are suggested by the "copy" part of the config, and make sure
            # to 'chmod a+x' them.
            if tarfile.is_tarfile(local_file):
                with tarfile.open(local_file) as tf:
                    members = tf.getmembers()
                    for (bin_name, from_name) in copypaths.items():
                        for member in members:
                            if member.name == from_name:
                                member.name = bin_name
                                tf.extract(member, self.local_path)
                                bin_path = os.path.join(
                                    self.local_path, bin_name)
                                os.chmod(
                                    bin_path, os.stat(bin_path).st_mode | stat.S_IEXEC)
                                break
                os.remove(local_file)

            # downloaded url is a zipfile.  Copy only the files out of the zipfile
            # that are suggested by the "copy" part of the config, and make sure
            # to 'chmod a+x' them.
            elif zipfile.is_zipfile(local_file):
                with zipfile.ZipFile(local_file) as zf:
                    members = zf.infolist()
                    for (bin_name, from_name) in copypaths.items():
                        for member in members:
                            if member.filename == from_name:
                                bin_path = os.path.join(
                                    self.local_path, bin_name)
                                source = zf.open(member)
                                target = open(bin_path, "wb")
                                with source, target:
                                    shutil.copyfileobj(source, target)
                                os.chmod(
                                    bin_path, os.stat(bin_path).st_mode | stat.S_IEXEC)
                os.remove(local_file)

            # this case doesn't really make sense, but is possible based on config
            # where you specified a download url and multiple copy paths.
            # I don't think it has any actual usecases, but I wrote it anyway.
            elif copypaths:
                for (bin_name, from_name) in copypaths.items():
                    bin_path = os.path.join(self.local_path, bin_name)
                    from_path = os.path.join(self.local_path, from_name)
                    os.rename(from_path, bin_path)
                    os.chmod(
                        bin_path, os.stat(bin_path).st_mode | stat.S_IEXEC)

            # In this case, you specified no `copy` items, so your URL must be
            # a single file that we downloaded.  Let's just make sure it is
            # executable.
            elif os.path.isfile(local_file):
                os.chmod(
                    local_file,
                    os.stat(local_file).st_mode | stat.S_IEXEC)
