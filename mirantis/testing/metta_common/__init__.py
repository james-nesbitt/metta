"""

Common METTA plugins

"""
from typing import Dict, Any

from configerus.loaded import LOADED_KEY_ROOT
from mirantis.testing.metta.plugin import Factory, Type
from mirantis.testing.metta.environment import Environment


from .common_config import add_common_config
from .dict_output import DictOutputPlugin
from .text_output import TextOutputPlugin
from .combo_provisioner import ComboProvisionerPlugin, COMBO_PROVISIONER_CONFIG_LABEL

METTA_PLUGIN_ID_OUTPUT_DICT = 'dict'
""" output plugin_id for the dict plugin """


@Factory(type=Type.OUTPUT, plugin_id=METTA_PLUGIN_ID_OUTPUT_DICT)
def metta_plugin_factory_output_dict(
        environment: Environment, instance_id: str = '', data: Dict = {}, validator: str = ''):
    """ create an output dict plugin """
    return DictOutputPlugin(environment, instance_id, data, validator)


METTA_PLUGIN_ID_OUTPUT_TEXT = 'text'
""" output plugin_id for the text plugin """


@Factory(type=Type.OUTPUT, plugin_id=METTA_PLUGIN_ID_OUTPUT_TEXT)
def metta_plugin_factory_output_text(
        environment: Environment, instance_id: str = '', text: str = ''):
    """ create an output text plugin """
    return TextOutputPlugin(environment, instance_id, text)


METTA_PLUGIN_ID_PROVISIONER_COMBO = 'combo'
""" provisioner plugin_id for the combo plugin """


@Factory(type=Type.PROVISIONER, plugin_id=METTA_PLUGIN_ID_PROVISIONER_COMBO)
def metta_plugin_factory_provisioner_combo(
        environment: Environment, instance_id: str = '', label: str = COMBO_PROVISIONER_CONFIG_LABEL, base: Any = LOADED_KEY_ROOT):
    """ create a provisioner combo plugin """
    return ComboProvisionerPlugin(
        environment, instance_id, label=label, base=base)


""" SetupTools EntryPoint BootStrapping """


def bootstrap(environment: Environment):
    """ METTA Bootstrapper - don't actually do anything """
    pass


""" METTA bootstraps that we will use on config objects """


def bootstrap_common(environment: Environment):
    """ metta configerus bootstrap

    Add some common Mirantis specific config options

    Add some common configerus sources for common data and common config source
    paths. Some of the added config is dynamic interpretation of environment,
    while also some default config paths are added if they can be interpeted

    @see .config.add_common_config() for details

    """
    add_common_config(environment)
