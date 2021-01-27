
import os.path
import appdirs
import pkg_resources

from mirantis.testing.mtt import plugin as mtt_plugin
from mirantis.testing.mtt.config import Config
from .plugins.config import ConfigSourceDictPlugin, ConfigSourcePathPlugin
from .plugins.provisioner import ExistingBackendProvisionerPlugin

MTT_PLUGIN_ID_CONFIGSOURCE_DICT = 'dict'
""" ConfigSource plugin_id for the mtt common dict plugin """
@mtt_plugin.Factory(type=mtt_plugin.Type.CONFIGSOURCE, plugin_id=MTT_PLUGIN_ID_CONFIGSOURCE_DICT)
def mtt_plugin_factory_configsource_dict(config: Config, instance_id: str = ''):
    """ create an mtt configsource dict plugin """
    return ConfigSourceDictPlugin(config, instance_id)

MTT_PLUGIN_ID_CONFIGSOURCE_PATH = 'path'
""" ConfigSource plugin_id for the mtt common path plugin """
@mtt_plugin.Factory(type=mtt_plugin.Type.CONFIGSOURCE, plugin_id=MTT_PLUGIN_ID_CONFIGSOURCE_PATH)
def mtt_plugin_factory_configsource_path(config: Config, instance_id: str = ''):
    """ create an mtt configsource path plugin """
    return ConfigSourcePathPlugin(config, instance_id)

MTT_PLUGIN_ID_PROVISIONER_EXISTING = 'existing'
""" Provisioner plugin_id for existing backend """
@mtt_plugin.Factory(type=mtt_plugin.Type.PROVISIONER, plugin_id=MTT_PLUGIN_ID_PROVISIONER_EXISTING)
def mtt_plugin_factory_configsource_path(config: Config, instance_id: str = ''):
    """ create an existing provsioner plugin """
    return ExistingBackendProvisionerPlugin(config, instance_id)

MTT_COMMON_APP_NAME = 'mtt'
""" config folder name in your user home folders somewhere sendible """
MTT_COMMON_DEFAULT_SOURCE_PRIORITY = 35
""" Config source priority for added config """
def add_common_config(config: Config, priority:int=MTT_COMMON_DEFAULT_SOURCE_PRIORITY):
    """ Add some common configuration sources """

    # a user config path (like ~/.config/mtt) may contain config
    user_conf_path = appdirs.user_config_dir(MTT_COMMON_APP_NAME)
    if os.path.exists(user_conf_path):
        config.add_source(MTT_PLUGIN_ID_CONFIGSOURCE_PATH, 'user', priority).set_path(user_conf_path)
