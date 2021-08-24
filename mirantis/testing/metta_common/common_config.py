"""

On bootstrap, add some common config values that can be useful to a project,
such as some information about the current user and current path, platform and
a fixed single datetime for operation.

This is optional, and may conflict or cloud some ways of using metta, so it is
only meant to be used when the infomration is useful.

"""
import os
import logging
import getpass
from datetime import datetime
import platform

import appdirs

from configerus.contrib.files import PLUGIN_ID_SOURCE_PATH as CONFIGERUS_SOURCE_PATH
from configerus.contrib.dict import PLUGIN_ID_SOURCE_DICT as CONFIGERUS_SOURCE_DICT
from mirantis.testing.metta.environment import Environment

logger = logging.getLogger("metta.common")

DIR = os.path.abspath(os.getcwd())

METTA_COMMON_APP_NAME = "metta"
""" used for some path building for config sources """
METTA_COMMON_CONFIG_USER_INSTANCE_ID = "user"
""" config source instance id for user path """
METTA_COMMON_CONFIG_PROJECT_DYNAMIC_INSTANCE_ID = "project_dynamic"
""" config source instance id for dynamic dict of commonly used value """
METTA_COMMON_DEFAULT_SOURCE_PRIORITY_DEFAULTS = 35
""" Config source priority for added common config """
METTA_COMMON_PROJECT_CONFIG_SUBPATH = "config"
""" convention for configuration path as a subfolder of the cwd path """

MARKER_FILES = {
    "metta.py",
    "mettac.py",
    "conftest.py",
    "pytest.ini",
}
""" Files which mark the root of a project """


def add_common_config(environment: Environment):
    """Add some common configuration sources.

    The following could be added:

    1. a `${PWD}/config` path source named "project_config" if that path exists
    2. a user defaults `~/metta` path source if that path exists
    3. a dynamic dict of common values:
        i. `user:id` pulled from the os
        ii. `global:datetime` to provide a constant datetime that can be used
           for consistent labelling
        iii `path:project` path to ${PWD} in case you want to build file paths
           based on that path

        @note we will likely grow this with common sense values

    Parameters:
    -----------
    environment (Environment) : METTA environment to be modified

    """

    # a user config path (like ~/.config/metta) may contain config
    user_conf_path = appdirs.user_config_dir(METTA_COMMON_APP_NAME)
    if not environment.config().has_source(METTA_COMMON_CONFIG_USER_INSTANCE_ID) and os.path.isdir(
        user_conf_path
    ):
        environment.config().add_source(
            CONFIGERUS_SOURCE_PATH,
            METTA_COMMON_CONFIG_USER_INSTANCE_ID,
            METTA_COMMON_DEFAULT_SOURCE_PRIORITY_DEFAULTS,
        ).set_path(user_conf_path)

    # Add some dymanic values for config
    environment.config().add_source(
        CONFIGERUS_SOURCE_DICT,
        METTA_COMMON_CONFIG_PROJECT_DYNAMIC_INSTANCE_ID,
        priority=METTA_COMMON_DEFAULT_SOURCE_PRIORITY_DEFAULTS,
    ).set_data(
        {
            "user": {"id": getpass.getuser()},  # override user id with a host value
            "environment": environment.info(),
            "global": {
                "datetime": datetime.now(),  # use a single datetime across all checks
            },
            environment.config().paths_label(): {  # config label for paths, usually just "paths"
                # you can use "paths:project" in config to substitute this path
                "project": find_project_root_path(DIR)
            },
            "platform": {
                "machine": platform.machine(),
                "system": platform.system(),
                "processor": platform.processor(),
                "version": platform.version(),
                "uname": platform.uname(),
            },
        }
    )


def find_project_root_path(start_path: str) -> str:
    """Find a project root path.

    We start looking in the cwd for certain marker files, and if we don't find
    any then we check the parent, recursively.

    If we never find a marker file then we assume that the current path is the
    root.

    """
    # Try to add a path from cwd and up that contains a mettac.py file
    check_path = start_path
    while check_path:
        if check_path == "/":
            break

        for marker_file in MARKER_FILES:
            marker_path = os.path.join(check_path, marker_file)
            if os.path.isfile(marker_path):
                return check_path

        check_path = os.path.dirname(check_path)

    return check_path
