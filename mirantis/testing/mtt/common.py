import os
import logging
import getpass
from datetime import datetime
import pkg_resources

import appdirs

from configerus.contrib.files import PLUGIN_ID_SOURCE_PATH as CONFIGERUS_SOURCE_PATH
from configerus.contrib.dict import PLUGIN_ID_SOURCE_DICT as CONFIGERUS_SOURCE_DICT
from uctt.environment import Environment
import mirantis.testing.mtt as mtt

logger = logging.getLogger("mtt.common")

DIR = os.path.abspath(os.getcwd())

MTT_COMMON_APP_NAME = "mtt"
""" used for some path building for config sources """
MTT_COMMON_CONFIG_USER_INSTANCE_ID = "user"
""" config source instance id for user path """
MTT_COMMON_CONFIG_PROJECT_CONFIG_INSTANCE_ID = "project_config"
""" config source instance id for project config path """
MTT_COMMON_CONFIG_PROJECT_DYNAMIC_INSTANCE_ID = "project_dynamic"
""" config source instance id for dynamic dict of commonly used value """
MTT_COMMON_DEFAULT_SOURCE_PRIORITY_DEFAULTS = 35
""" Config source priority for added common config """
MTT_COMMON_PROJECT_CONFIG_SUBPATH = "config"
""" convention for configuration path as a subfolder of the cwd path """
MTT_PATH_NAME = "mtt"
""" This config label will be loaded to interpret config in add_common_config """
MTT_PATH = pkg_resources.resource_filename("mirantis.testing.mtt", "")
""" Path to the mtt project root """
MTT_CONFIG_PATH = pkg_resources.resource_filename(
    "mirantis.testing.mtt", "config")
""" Path to the MTT Mirantis config preset configurations """


def add_common_config(environment: Environment):
    """ Add some common configuration sources

    The following could be added:

    1. a `${PWD}/config` path source named "project_config" if that path exists
    2. a user defaults `~/mtt` path source if that path exists
    3. a dynamic dict of common values:
        i. `user:id` pulled from the os
        ii. `global:datetime` to provide a constant datetime that can be used
           for consistent labelling
        iii `path:project` path to ${PWD} in case you want to build file paths
           based on that path

        @note we will likely grow this with common sense values

    Parameters:
    -----------

    environment (Environment) : UCTT environment to be modified

    """

    project_root_path = find_project_root_path()

    # a user config path (like ~/.config/mtt) may contain config
    user_conf_path = appdirs.user_config_dir(MTT_COMMON_APP_NAME)
    if not environment.config.has_source(
            MTT_COMMON_CONFIG_USER_INSTANCE_ID) and os.path.isdir(user_conf_path):
        environment.config.add_source(
            CONFIGERUS_SOURCE_PATH,
            MTT_COMMON_CONFIG_USER_INSTANCE_ID,
            MTT_COMMON_DEFAULT_SOURCE_PRIORITY_DEFAULTS).set_path(user_conf_path)

    # Add a ${PWD}/config path as a config source if it exists
    project_config_path = os.path.join(
        project_root_path,
        MTT_COMMON_PROJECT_CONFIG_SUBPATH)
    if not environment.config.has_source(
            MTT_COMMON_CONFIG_PROJECT_CONFIG_INSTANCE_ID) and os.path.isdir(project_config_path):
        environment.config.add_source(
            CONFIGERUS_SOURCE_PATH,
            MTT_COMMON_CONFIG_PROJECT_CONFIG_INSTANCE_ID).set_path(project_config_path)

    # Add some dymanic values for config
    environment.config.add_source(CONFIGERUS_SOURCE_DICT, MTT_COMMON_CONFIG_PROJECT_DYNAMIC_INSTANCE_ID, MTT_COMMON_DEFAULT_SOURCE_PRIORITY_DEFAULTS).set_data({
        "user": {
            "id": getpass.getuser()  # override user id with a host value
        },
        "global": {
            "datetime": datetime.now(),  # use a single datetime across all checks
        },
        environment.config.paths_label(): {  # special config label for file paths, usually just "paths"
            # you can use "paths:project" in config to substitute this path
            "project": project_root_path
        }
    })

    # Add a "{path:mtt}" config value so that paths to this module can
    # be built.  We use this to allow file resources from this module to be used
    # as a part of config.  For example we build paths to the terraform plans in
    # this module.
    mtt_paths_instance_id = "{}-paths".format(MTT_COMMON_APP_NAME)
    if not environment.config.has_source(mtt_paths_instance_id):
        environment.config.add_source(CONFIGERUS_SOURCE_DICT, mtt_paths_instance_id).set_data({
            environment.config.paths_label(): {
                MTT_PATH_NAME: MTT_PATH
            }
        })

    # If we haven't already done it, add the mtt/config path as a
    # config source.  This allows us to provide config defaults in this module
    mtt_common_instance_id = MTT_COMMON_APP_NAME
    if not environment.config.has_source(mtt_common_instance_id):
        environment.config.add_source(
            CONFIGERUS_SOURCE_PATH,
            mtt_common_instance_id).set_path(MTT_CONFIG_PATH)


def find_project_root_path():
    """ try to find a project root path

    We start looking in the cwd for certain marker files, and if we don't find
    any then we check the parent, recursively.

    If we never find a marker file then we assume that the current path is the
    root.

    """

    MARKER_FILES = {
        'uctt.py',
        'ucttc.py',
        'conftest.py',
        'pytest.ini',
    }

    # Try to add a path from cwd and up that contains a ucttc.py file
    check_path = DIR
    while check_path:
        if check_path == '/':
            return DIR

        for MARKER_FILE in MARKER_FILES:
            marker_path = os.path.join(check_path, MARKER_FILE)
            if os.path.isfile(marker_path):
                return check_path

        check_path = os.path.dirname(check_path)
