"""

METTA PLUGIN: bin download helper.

A helper plugin for downloading executables from the internet to help other
Plugins which might rely on external executables.

@NOTE remote urls may be tarballs/zips

@NOTE it goes without saying that downloading executables comes with an inherit
risk.  The request validates any certs, but it is up to you to make sure that
no config is in place which downloads dangerous bins.

The idea here is that you can tell your system to put bins from a list of
urls into a path, and have that path included in PATH in your python
environment. If you want, use a common system path like '/usr/local/bin' or
use a temporary or local path if you want to isolate versions for your test
suite.

There are two ways you can use this:

1. put a list of bins into the plugin config, and it will download when it is
constructed.  This de-couples acquiring bins from plugins that may use them, and
does all of the downloading up front before all fixtures are created.
If another fixture needs a bin in its own constructor, just make sure that this
fixture is created first.

2. any other code with access to the environment can access the binhelper
plugin and provide details to the `get_bin` method.  This couples the plugins,
and means that you will have to ensure that this plugin is available and handle
dependencies yourself.

"""
from typing import Dict
import shutil
import os
import logging
import tarfile
import zipfile
import re
import stat
import platform

import requests

from configerus.loaded import LOADED_KEY_ROOT
from configerus.contrib.jsonschema.validate import (
    PLUGIN_ID_VALIDATE_JSONSCHEMA_SCHEMA_CONFIG_LABEL,
)
from configerus.validator import ValidationError

from mirantis.testing.metta.environment import Environment

logger = logging.getLogger("metta.common.utility:binhelper")

METTA_PLUGIN_ID_UTILITY_BINHELPER = "bin-helper-utility"
""" metta utility plugin_id for the bin-helper plugin """

BINHELPER_UTILITY_CONFIG_LABEL = "binhelper"
""" Config label used by default to load binhelper configuration """

BINHELPER_UTILITY_CONFIG_BASE_LOCALPATH = "path.local"
""" config base for what the local bin path should be """
BINHELPER_UTILITY_CONFIG_BASE_ADDTOPATH = "path.add_to_path"
""" config base for if we need to modify the env PATH and add the path """
BINHELPER_UTILITY_CONFIG_BASE_PLATFORMS = "platforms"
""" config base for list of platform bins to load on construction """

BINHELPER_UTILITY_CONFIG_BASE_BIN_URL = "url"
""" config base inside bin for bin url for downloading """
BINHELPER_UTILITY_CONFIG_BASE_BIN_VERSION = "version"
""" config base inside bin for bin version """
BINHELPER_UTILITY_CONFIG_BASE_BIN_COPYPATHS = "copy"
""" config base inside bin for a map of bins name->path-inpackage """

BINHELPER_CONFIG_JSONSCHEMA = {
    "type": "object",
    "path": {
        "type": "object",
        "properties": {"local": {"type": "string"}, "add_to_environ": {"type": "bool"}},
        "required": ["path"],
    },
    "platforms": {"$ref": "#/definitions/platform"},
    "definitions": {
        "bin": {
            "type": "object",
            "properties": {
                "url": {"type": "string"},
                "version": {"type": "string"},
                "copy": {"type": "object"},
            },
            "required": ["url"],
        },
        "platform": {"$ref": "#/definitions/bin"},
    },
    "required": ["path", "platforms"],
}
""" JSONSCHEMA for the binhelper config """
BINHELPER_CONFIG_VALIDATE_TARGET = {
    PLUGIN_ID_VALIDATE_JSONSCHEMA_SCHEMA_CONFIG_LABEL: BINHELPER_CONFIG_JSONSCHEMA
}
""" configerus validate target for binhelper config """


# This needs to be a metta plugin
# pylint: disable=too-few-public-methods
class DownloadableExecutableUtility:
    """A helper to help you download executables."""

    def __init__(
        self,
        environment: Environment,
        instance_id: str,
        label: str = BINHELPER_UTILITY_CONFIG_LABEL,
        base: str = LOADED_KEY_ROOT,
    ):
        """Perform initial plugin configuration.

        Parameters:
        -----------
        envirionment (Environment) : environment in which this plugin exists.
        instance_id (str) : string id of this plugin instance.

        label (str) : Configerus config load label for accessing plugin
            instance config.
        base (Any) : Configerus config get key for a base that contains all
            plugin instance config.

        """
        self._environment: Environment = environment
        """ Environemnt in which this plugin exists """
        self._instance_id: str = instance_id
        """ Unique id for this plugin instance """

        loaded = self._environment.config().load(label)
        try:
            loaded.get(base, validator=BINHELPER_CONFIG_VALIDATE_TARGET)
        except KeyError as err:
            raise ValueError("Bin-Helper configuration is missing") from err
        except ValidationError as err:
            raise ValueError("Bin-Helper received invalid configuration") from err

        self.local_path = loaded.get([base, BINHELPER_UTILITY_CONFIG_BASE_LOCALPATH])

        add_to_path = loaded.get([base, BINHELPER_UTILITY_CONFIG_BASE_ADDTOPATH])
        if add_to_path:
            os.environ["PATH"] += os.pathsep + os.path.realpath(self.local_path)

        platforms = loaded.get([base, BINHELPER_UTILITY_CONFIG_BASE_PLATFORMS])
        current_platform = f"{platform.system()}-{platform.machine()}"

        if current_platform not in platforms:
            logger.warning(
                "BinHelper doesn't have configuration for your platform '%s', so it "
                "won't download any bins.",
                current_platform,
            )
            return

        bins = platforms[current_platform]
        for bin_id in list(bins.keys()):
            url = loaded.get(
                [
                    base,
                    BINHELPER_UTILITY_CONFIG_BASE_PLATFORMS,
                    current_platform,
                    bin_id,
                    BINHELPER_UTILITY_CONFIG_BASE_BIN_URL,
                ]
            )
            copypaths = loaded.get(
                [
                    base,
                    BINHELPER_UTILITY_CONFIG_BASE_PLATFORMS,
                    current_platform,
                    bin_id,
                    BINHELPER_UTILITY_CONFIG_BASE_BIN_COPYPATHS,
                ]
            )
            self.get_bin(name=bin_id, url=url, copypaths=copypaths)

    def get_bin(self, name: str, url: str, copypaths: Dict[str, str] = None):
        """Get a remote bin package, and put any bin contents into a bin path.

        Make sure that we have the bin in scope; download it if we don't

        """
        path = shutil.which(name, os.X_OK)

        if path is None:
            logger.info("bin-helper can't find %s. Downloading it from %s", name, url)

            # First get the url
            with requests.get(url, allow_redirects=True) as res:
                res.raise_for_status()

                # try to decide on a name for the download
                file_name = None
                content_disposition = res.headers.get("content-disposition")
                if content_disposition is not None:
                    file_name_matches = re.findall("filename=(.+)", content_disposition)
                    if file_name_matches:
                        file_name = file_name_matches[0]
                if file_name is None:
                    # @NOTE this may not be a reliable way of getting a name from a url
                    file_name = os.path.basename(url)

                # write the file into our local path
                local_file = os.path.join(self.local_path, file_name)
                with open(local_file, "wb") as fil:
                    fil.write(res.content)

            # downloaded url is a tarfile.  Copy only the files out of the tarfile
            # that are suggested by the "copy" part of the config, and make sure
            # to 'chmod a+x' them.
            if tarfile.is_tarfile(local_file):
                _untar(local_file, self.local_path, copypaths)
                os.remove(local_file)

            # downloaded url is a zipfile.  Copy only the files out of the zipfile
            # that are suggested by the "copy" part of the config, and make sure
            # to 'chmod a+x' them.
            elif zipfile.is_zipfile(local_file):
                _unzip(local_file, self.local_path, copypaths)
                os.remove(local_file)

            # this case doesn't really make sense, but is possible based on config
            # where you specified a download url and multiple copy paths.
            # I don't think it has any actual usecases, but I wrote it anyway.
            elif copypaths:
                _copyfiles(self.local_path, copypaths)

            # In this case, you specified no `copy` items, so your URL must be
            # a single file that we downloaded.  Let's just make sure it is
            # executable.
            elif os.path.isfile(local_file):
                os.chmod(local_file, os.stat(local_file).st_mode | stat.S_IEXEC)


def _untar(local_file, local_path, copypaths):
    """Untar a file.

    Extract, copy and chmod executables out of a tar file.

    """
    with tarfile.open(local_file) as taf:
        members = taf.getmembers()
        for (bin_name, from_name) in copypaths.items():
            for member in members:
                if member.name == from_name:
                    member.name = bin_name
                    taf.extract(member, local_path)
                    bin_path = os.path.join(local_path, bin_name)
                    os.chmod(bin_path, os.stat(bin_path).st_mode | stat.S_IEXEC)
                    break


def _unzip(local_file, local_path, copypaths):
    """Unzip a file.

    Extract, copy and chmod executables out of a zip file.

    """
    with zipfile.ZipFile(local_file) as zif:
        members = zif.infolist()
        for (bin_name, from_name) in copypaths.items():
            for member in members:
                if member.filename == from_name:
                    bin_path = os.path.join(local_path, bin_name)
                    with zif.open(member) as source, open(bin_path, "wb") as target:
                        shutil.copyfileobj(source, target)
                    os.chmod(bin_path, os.stat(bin_path).st_mode | stat.S_IEXEC)


def _copyfiles(local_path, copypaths):
    """Copy files from one path to another.

    Just move and chmod files from one path to another, and chmod executables.

    """
    for (bin_name, from_name) in copypaths.items():
        bin_path = os.path.join(local_path, bin_name)
        from_path = os.path.join(local_path, from_name)
        os.rename(from_path, bin_path)
        os.chmod(bin_path, os.stat(bin_path).st_mode | stat.S_IEXEC)
