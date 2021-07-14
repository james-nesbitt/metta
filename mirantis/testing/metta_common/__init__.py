"""

Common METTA plugins and functionality.

Package for common shared Metta plugins that can be used by various
other plugins as a based.

"""
from typing import Dict, Any

from configerus import Config
from configerus.loaded import LOADED_KEY_ROOT
from configerus.plugin import FormatFactory

from mirantis.testing.metta.plugin import Factory
from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.provisioner import METTA_PLUGIN_INTERFACE_ROLE_PROVISIONER
from mirantis.testing.metta.workload import METTA_PLUGIN_INTERFACE_ROLE_WORKLOAD
from mirantis.testing.metta.output import METTA_PLUGIN_INTERFACE_ROLE_OUTPUT
from mirantis.testing.metta_cli.base import METTA_PLUGIN_INTERFACE_ROLE_CLI

from .common_config import add_common_config
from .dict_output import DictOutputPlugin, METTA_PLUGIN_ID_OUTPUT_DICT
from .text_output import TextOutputPlugin, METTA_PLUGIN_ID_OUTPUT_TEXT
from .combo_provisioner import (
    ComboProvisionerPlugin,
    METTA_PLUGIN_ID_PROVISIONER_COMBO,
    COMBO_PROVISIONER_CONFIG_LABEL,
)
from .healthpoll_workload import (
    HealthPollWorkload,
    METTA_PLUGIN_ID_WORKLOAD_HEALTHPOLL,
    HEALTHPOLL_CONFIG_LABEL,
)
from .binhelper_utility import (
    DownloadableExecutableUtility,
    METTA_PLUGIN_ID_UTILITY_BINHELPER,
    BINHELPER_UTILITY_CONFIG_LABEL,
)
from .config_format_output import ConfigFormatOutputPlugin, PLUGIN_ID_FORMAT_OUTPUT
from .user_cli import UserCliPlugin, METTA_PLUGIN_ID_CLI_USER

METTA_PLUGIN_INTERFACE_ROLE_UTILITY = "utility"
""" metta pluging_type for utility plugins """


@Factory(
    plugin_id=METTA_PLUGIN_ID_OUTPUT_DICT,
    interfaces=[METTA_PLUGIN_INTERFACE_ROLE_OUTPUT],
)
def metta_plugin_factory_output_dict(
    environment: Environment,
    instance_id: str = "",
    data: Dict = None,
    validator: str = "",
):
    """Create an output dict plugin."""
    return DictOutputPlugin(environment, instance_id, data, validator)


@Factory(
    plugin_id=METTA_PLUGIN_ID_OUTPUT_TEXT,
    interfaces=[METTA_PLUGIN_INTERFACE_ROLE_OUTPUT],
)
def metta_plugin_factory_output_text(
    environment: Environment, instance_id: str = "", text: str = ""
):
    """Create an output text plugin."""
    return TextOutputPlugin(environment, instance_id, text)


@Factory(
    plugin_id=METTA_PLUGIN_ID_PROVISIONER_COMBO,
    interfaces=[METTA_PLUGIN_INTERFACE_ROLE_PROVISIONER],
)
def metta_plugin_factory_provisioner_combo(
    environment: Environment,
    instance_id: str = "",
    label: str = COMBO_PROVISIONER_CONFIG_LABEL,
    base: Any = LOADED_KEY_ROOT,
):
    """Create a provisioner combo plugin."""
    return ComboProvisionerPlugin(environment, instance_id, label=label, base=base)


@Factory(
    plugin_id=METTA_PLUGIN_ID_UTILITY_BINHELPER,
    interfaces=[METTA_PLUGIN_INTERFACE_ROLE_UTILITY],
)
def metta_plugin_factory_utility_binhelper(
    environment: Environment,
    instance_id: str = "",
    label: str = BINHELPER_UTILITY_CONFIG_LABEL,
    base: Any = LOADED_KEY_ROOT,
):
    """Create a bin-helper utility plugin."""
    return DownloadableExecutableUtility(
        environment, instance_id, label=label, base=base
    )


@Factory(
    plugin_id=METTA_PLUGIN_ID_WORKLOAD_HEALTHPOLL,
    interfaces=[METTA_PLUGIN_INTERFACE_ROLE_WORKLOAD],
)
def metta_plugin_factory_workload_healthpoll(
    environment: Environment,
    instance_id: str = "",
    label: str = HEALTHPOLL_CONFIG_LABEL,
    base: Any = LOADED_KEY_ROOT,
):
    """Create an metta health polling workload plugin."""
    return HealthPollWorkload(environment, instance_id, label=label, base=base)


# ----- Congiferus formatter for metta output plugins -----


@FormatFactory(plugin_id=PLUGIN_ID_FORMAT_OUTPUT)
def plugin_factory_format_output(config: Config, instance_id: str = ""):
    """Create an format plugin which replaces from output contents."""
    return ConfigFormatOutputPlugin(config, instance_id)


# ----- metta user cli plugin -----


@Factory(
    plugin_id=METTA_PLUGIN_ID_CLI_USER, interfaces=[METTA_PLUGIN_INTERFACE_ROLE_CLI]
)
def metta_plugin_factory_user_config(environment: Environment, instance_id: str = ""):
    """Create a user cli plugin."""
    return UserCliPlugin(environment, instance_id)


# ----- METTA bootstraps that we will use on config objects -----


# pylint: disable=unused-argument
def bootstrap(environment: Environment):
    """METTA_Terraform bootstrap.

    Currently we only use this to import plugins.

    Parameters:
    -----------
    env (Environment) : an environment which should have validation config added to.

    """


def bootstrap_common(environment: Environment):
    """Metta configerus bootstrap.

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
        priority=40,
    )
    output_formatter.set_environemnt(environment)
