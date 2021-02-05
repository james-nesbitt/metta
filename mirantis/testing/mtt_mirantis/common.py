import os
import logging
import getpass
from datetime import datetime
import pkg_resources

import appdirs
from configerus.config import Config

import mirantis.testing.mtt as mtt

logger = logging.getLogger('mtt_mirantis.common')

DIR = os.getcwd()

MTT_COMMON_APP_NAME = 'mtt'
""" used for some path building for config sources """
MTT_COMMON_CONFIG_USER_INSTANCE_ID = 'user'
""" config source instance id for user path """
MTT_COMMON_CONFIG_PROJECT_CONFIG_INSTANCE_ID = 'project_config'
""" config source instance id for project config path """
MTT_COMMON_CONFIG_PROJECT_DYNAMIC_INSTANCE_ID = 'project_dynamic'
""" config source instance id for dynamic dict of commonly used value """
MTT_COMMON_DEFAULT_SOURCE_PRIORITY_DEFAULTS = 35
""" Config source priority for added common config """
MTT_COMMON_PROJECT_CONFIG_SUBPATH = "config"
""" convention for configuration path as a subfolder of the cwd path """
MTT_MIRANTIS_PATH_NAME = 'mtt_mirantis'
""" This config label will be loaded to interpret config in config_interpret_mtt_mirantis """
MTT_MIRANTIS_PATH=pkg_resources.resource_filename('mirantis.testing.mtt_mirantis', '')
""" Path to the mtt_mirantis project root """
MTT_MIRANTIS_CONFIG_PATH=pkg_resources.resource_filename('mirantis.testing.mtt_mirantis', 'config')
""" Path to the MTT Mirantis config preset configurations """

def add_common_config(config:Config):
    """ Add some common configuration sources

    The following could be added:

    1. a `${PWD}/config` path source named 'project_config' if that path exists
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

    config (Config) : a configerus.config.Config object which will be modified

    """

    # a user config path (like ~/.config/mtt) may contain config
    user_conf_path = appdirs.user_config_dir(MTT_COMMON_APP_NAME)
    if not config.has_source(MTT_COMMON_CONFIG_USER_INSTANCE_ID) and os.path.isdir(user_conf_path):
        config.add_source(mtt.CONFIGSOURCE_PATH, MTT_COMMON_CONFIG_USER_INSTANCE_ID, MTT_COMMON_DEFAULT_SOURCE_PRIORITY_DEFAULTS).set_path(user_conf_path)

    # Add a ${PWD}/config path as a config source if it exists
    project_config_path = os.path.join(DIR, MTT_COMMON_PROJECT_CONFIG_SUBPATH)
    if not config.has_source(MTT_COMMON_CONFIG_PROJECT_CONFIG_INSTANCE_ID) and os.path.isdir(project_config_path):
        config.add_source(mtt.CONFIGSOURCE_PATH, MTT_COMMON_CONFIG_PROJECT_CONFIG_INSTANCE_ID).set_path(project_config_path)
    # Add some dymanic values for config
    config.add_source(mtt.CONFIGSOURCE_DICT, MTT_COMMON_CONFIG_PROJECT_DYNAMIC_INSTANCE_ID, MTT_COMMON_DEFAULT_SOURCE_PRIORITY_DEFAULTS).set_data({
        "user": {
            "id": getpass.getuser() # override user id with a host value
        },
        "global": {
            "datetime": datetime.now(), # use a single datetime across all checks
        },
        config.paths_label(): { # special config label for file paths, usually just 'paths'
            "project": DIR  # you can use 'paths:project' in config to substitute this path
        }
    })

    # Add a '{path:mtt_mirantis}' config value so that paths to this module can
    # be built.  We use this to allow file resources from this module to be used
    # as a part of config.  For example we build paths to the terraform plans in
    # this module.
    mtt_mirantis_paths_instance_id = "{}-paths".format(MTT_COMMON_APP_NAME)
    if not config.has_source(mtt_mirantis_paths_instance_id):
        config.add_source(mtt.CONFIGSOURCE_DICT, mtt_mirantis_paths_instance_id).set_data({
            config.paths_label(): {
                MTT_MIRANTIS_PATH_NAME: MTT_MIRANTIS_PATH
            }
        })

    # If we haven't already done it, add the mtt_mirantis/config path as a
    # config source.  This allows us to provide config defaults in this module
    mtt_mirantis_common_instance_id = MTT_COMMON_APP_NAME
    if not config.has_source(mtt_mirantis_common_instance_id):
        config.add_source(mtt.CONFIGSOURCE_PATH, mtt_mirantis_common_instance_id).set_path(MTT_MIRANTIS_CONFIG_PATH)
