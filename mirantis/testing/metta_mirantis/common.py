import logging
import pkg_resources

import appdirs

from configerus.contrib.files import PLUGIN_ID_SOURCE_PATH as CONFIGERUS_SOURCE_PATH
from configerus.contrib.dict import PLUGIN_ID_SOURCE_DICT as CONFIGERUS_SOURCE_DICT

from mirantis.testing.metta.environment import Environment

logger = logging.getLogger("metta_mirantis.common")

METTA_MIRANTIS_COMMON_NAME = "metta-mirantis"
""" used for some path building for config sources """
METTA_MIRANTIS_COMMON_DEFAULT_SOURCE_PRIORITY_DEFAULTS = 35
""" Config source priority for added common config """
METTA_MIRANTIS_PATH = pkg_resources.resource_filename(
    "mirantis.testing.metta_mirantis", "")
""" Path to the metta mirantis project root """
METTA_MIRANTIS_CONFIG_PATH = pkg_resources.resource_filename(
    'mirantis.testing.metta_mirantis', "config")
""" Path to the metta mirantis config preset configurations """


def add_common_config(environment: Environment):
    """ Add some common configuration sources

    The following could be added:

    1. a path config key for a path to this module.  This is used to make it
       easier to build paths to things like the terraform plans in this package
    2. add this module's ./config path as a config source.

    Parameters:
    -----------

    environment (Environment) : METTA environment to be modified

    """

    # If we haven't already done it, add the metta_mirantis/config path as a
    # config source.  This allows us to provide config defaults in this module
    metta_mirantis_config_instance_id = "{}-config".format(
        METTA_MIRANTIS_COMMON_NAME)
    if not environment.config.has_source(metta_mirantis_config_instance_id):
        environment.config.add_source(
            CONFIGERUS_SOURCE_PATH,
            metta_mirantis_config_instance_id,
            priority=METTA_MIRANTIS_COMMON_DEFAULT_SOURCE_PRIORITY_DEFAULTS).set_path(METTA_MIRANTIS_CONFIG_PATH)

    # Add a "{path:metta_mirantis}" config value so that paths to this module can
    # be built.  We use this to allow file resources from this module to be used
    # as a part of config.  For example we build paths to the terraform plans in
    # this module.
    metta_mirantis_paths_instance_id = "{}-paths".format(
        METTA_MIRANTIS_COMMON_NAME)
    if not environment.config.has_source(metta_mirantis_paths_instance_id):
        environment.config.add_source(CONFIGERUS_SOURCE_DICT, metta_mirantis_paths_instance_id, priority=METTA_MIRANTIS_COMMON_DEFAULT_SOURCE_PRIORITY_DEFAULTS).set_data({
            environment.config.paths_label(): {
                METTA_MIRANTIS_COMMON_NAME: METTA_MIRANTIS_PATH
            }
        })
