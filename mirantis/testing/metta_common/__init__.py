"""

Common METTA plugins

"""
from typing import Dict, Any

from configerus import Config
from configerus.loaded import LOADED_KEY_ROOT
from configerus.plugin import FormatFactory

from mirantis.testing.metta.plugin import Factory, Type
from mirantis.testing.metta.environment import Environment

from .common_config import add_common_config
from .dict_output import DictOutputPlugin
from .text_output import TextOutputPlugin
from .combo_provisioner import ComboProvisionerPlugin, COMBO_PROVISIONER_CONFIG_LABEL
from .binhelper_utility import DownloadableExecutableUtility, METTA_PLUGIN_ID_UTILITY_BINHELPER, BINHELPER_UTILITY_CONFIG_LABEL
from .config_format_output import ConfigFormatOutputPlugin
from .user_cli import UserCliPlugin

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


@Factory(type=Type.UTILITY, plugin_id=METTA_PLUGIN_ID_UTILITY_BINHELPER)
def metta_plugin_factory_utility_binhelper(
        environment: Environment, instance_id: str = '', label: str = BINHELPER_UTILITY_CONFIG_LABEL, base: Any = LOADED_KEY_ROOT):
    """ create a bin-helper utility plugin """
    return DownloadableExecutableUtility(
        environment, instance_id, label=label, base=base)


""" Congiferus formatter for metta output plugins """

PLUGIN_ID_FORMAT_OUTPUT = 'output'
""" Format plugin_id for the configerus output format plugin """


@FormatFactory(plugin_id=PLUGIN_ID_FORMAT_OUTPUT)
def plugin_factory_format_output(config: Config, instance_id: str = ''):
    """ create an format plugin which replaces from output contents """
    return ConfigFormatOutputPlugin(config, instance_id)


""" metta user cli plugin """

METTA_PLUGIN_ID_CLI_USER = 'user'
""" cli plugin_id for the user plugin """


@Factory(type=Type.CLI, plugin_id=METTA_PLUGIN_ID_CLI_USER)
def metta_plugin_factory_user_config(
        environment: Environment, instance_id: str = ''):
    """ create a user cli plugin """
    return UserCliPlugin(environment, instance_id)


""" METTA bootstraps that we will use on config objects """


def bootstrap(environment: Environment):
    """ METTA Bootstrapper - don't actually do anything """
    pass

# @TODO this should be renamed on the next major version bump.


def bootstrap_common(environment: Environment):
    """ metta configerus bootstrap

    Add some common Mirantis specific config options

    Add some common configerus sources for common data and common config source
    paths. Some of the added config is dynamic interpretation of environment,
    while also some default config paths are added if they can be interpeted

    @see .config.add_common_config() for details

    """
    add_common_config(environment)

    # Add a configerus output formatter which can interpret environemnt
    # outputs.
    output_formatter = environment.config.add_formatter(
        plugin_id=PLUGIN_ID_FORMAT_OUTPUT,
        instance_id=PLUGIN_ID_FORMAT_OUTPUT,
        priority=40)
    output_formatter.set_environemnt(environment)
