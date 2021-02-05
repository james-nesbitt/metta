"""

MTT Mirantis


"""
from typing import List
import os

from configerus.config import Config

from mirantis.testing.mtt import plugin as mtt_plugin

from .common import add_common_config
from .presets import add_preset_config
from .plugins.launchpad import LaunchpadProvisionerPlugin
from .plugins.existing import ExistingBackendProvisionerPlugin

MTT_LAUNCHPAD_PROVISIONER_PLUGIN_ID = 'mtt_launchpad'
""" provisioner plugin_id for the launchpad plugin """
@mtt_plugin.Factory(type=mtt_plugin.Type.PROVISIONER, plugin_id=MTT_LAUNCHPAD_PROVISIONER_PLUGIN_ID)
def mtt_plugin_factory_provisioner_launchpad(config:Config, instance_id:str=''):
    """ create a launchpad provisioner plugin """
    return LaunchpadProvisionerPlugin(config, instance_id)

MTT_EXISTING_PROVISIONER_PLUGIN_ID = 'existing'
""" Provisioner plugin_id for existing backend """
@mtt_plugin.Factory(type=mtt_plugin.Type.PROVISIONER, plugin_id=MTT_EXISTING_PROVISIONER_PLUGIN_ID)
def mtt_plugin_factory_configsource_path(config:Config, instance_id: str = ''):
    """ create an existing provsioner plugin """
    return ExistingBackendProvisionerPlugin(config, instance_id)

""" CONFIGERUS BOOTSTRAPPERS """

""" configerus bootstraps that we will use on config objects """
def configerus_bootstrap_all(config:Config):
    """ MTT_Mirantis configerus bootstrap

    Add some Mirantis specific config options

    run bootstrapping for both common and presets

    """
    configerus_bootstrap_common(config)
    configerus_bootstrap_presets(config)

""" configerus bootstraps that we will use on config objects """
def configerus_bootstrap_common(config:Config):
    """ MTT_Mirantis configerus bootstrap

    Add some Mirantis specific config options

    Add some common configerus sources for common data and common config source
    paths. Some of the added config is dynamic interpretation of environment,
    while also some default config paths are added if they can be interpeted

    @see .config.add_common_config() for details

    """
    add_common_config(config)

""" configerus bootstraps that we will use on config objects """
def configerus_bootstrap_presets(config:Config):
    """ MTT_Mirantis configerus bootstrap

    Add some Mirantis specific config options

    Additional config sources may be added based on config.load('mtt_mirantis')
    which will try to add config for mtt_mirantis `presets`
    This gives access to 'variation', 'cluster', 'platform' and 'release'
    presets.  You can dig deeper, but it might implicitly make sense if you look
    at the config folder of this module.

    @see .presets.add_preset_config() for details

    """
    add_preset_config(config)
