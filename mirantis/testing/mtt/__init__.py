"""

MTT Mirantis


"""

from typing import List
import os

from configerus.config import Config as configerus_Config
from configerus.contrib.dict import PLUGIN_ID_SOURCE_DICT as CONFIGERUS_SOURCE_DICT
from configerus.contrib.files import PLUGIN_ID_SOURCE_PATH as CONFIGERUS_SOURCE_PATH
from uctt import bootstrap as uctt_bootstrap
from uctt.plugin import Factory as uctt_Factory, Type as uctt_Type

from .common import add_common_config
from .presets import add_preset_config
from .launchpad import LaunchpadProvisionerPlugin

""" GENERATING CONFIG  """

# Local shortcuts to the configerus contrib source plugins
# which simplify imports for consumers
SOURCE_DICT = CONFIGERUS_SOURCE_DICT
""" Configerus plugin_id for Dict source """
SOURCE_PATH = CONFIGERUS_SOURCE_PATH
""" Configerus plugin_id for Path source """

MTT_LAUNCHPAD_PROVISIONER_PLUGIN_ID = "mtt_launchpad"
""" provisioner plugin_id for the launchpad plugin """


@uctt_Factory(type=uctt_Type.PROVISIONER,
              plugin_id=MTT_LAUNCHPAD_PROVISIONER_PLUGIN_ID)
def mtt_plugin_factory_provisioner_launchpad(
        config: configerus_Config, instance_id: str = ""):
    """ create a launchpad provisioner plugin """
    return LaunchpadProvisionerPlugin(config, instance_id)


""" UCTT BOOTSTRAPPERS """

""" UCTT bootstraps that we will use on config objects """


def uctt_bootstrap_all(config: configerus_Config):
    """ MTT configerus bootstrap

    Add some Mirantis specific config options

    run bootstrapping for both common and presets

    """
    uctt_bootstrap_common(config)
    uctt_bootstrap_presets(config)


""" UCTT bootstraps that we will use on config objects """


def uctt_bootstrap_common(config: configerus_Config):
    """ MTT configerus bootstrap

    Add some common Mirantis specific config options

    Add some common configerus sources for common data and common config source
    paths. Some of the added config is dynamic interpretation of environment,
    while also some default config paths are added if they can be interpeted

    @see .config.add_common_config() for details

    """
    add_common_config(config)


""" UCTT bootstraps that we will use on config objects """


def uctt_bootstrap_presets(config: configerus_Config):
    """ MTT configerus bootstrap

    Add some Mirantis specific config options for presets

    Additional config sources may be added based on config.load("mtt")
    which will try to add config for mtt `presets`
    This gives access to "variation", "cluster", "platform" and "release"
    presets.  You can dig deeper, but it might implicitly make sense if you look
    at the config folder of this module.

    @see .presets.add_preset_config() for details

    """
    add_preset_config(config)
