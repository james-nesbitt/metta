"""

METTA Cli package.

"""

import logging

from mirantis.testing.metta.plugin import Factory
from mirantis.testing.metta.environment import Environment

from .base import METTA_PLUGIN_INTERFACE_ROLE_CLI
from .config import ConfigCliPlugin
from .environment import EnvironmentCliPlugin
from .fixtures import FixturesCliPlugin
from .provisioner import ProvisionerCliPlugin
from .output import OutputCliPlugin

logger = logging.getLogger("metta.cli")


METTA_PLUGIN_ID_CLI_CONFIG = "config_cli"
""" cli plugin_id for the config plugin """


@Factory(plugin_id=METTA_PLUGIN_ID_CLI_CONFIG, interfaces=[METTA_PLUGIN_INTERFACE_ROLE_CLI])
def metta_plugin_factory_cli_config(environment: Environment, instance_id: str = ""):
    """Create a config cli plugin."""
    return ConfigCliPlugin(environment, instance_id)


METTA_PLUGIN_ID_CLI_ENVIRONMENT = "environment_cli"
""" cli plugin_id for the environment plugin """


@Factory(
    plugin_id=METTA_PLUGIN_ID_CLI_ENVIRONMENT,
    interfaces=[METTA_PLUGIN_INTERFACE_ROLE_CLI],
)
def metta_plugin_factory_cli_environment(environment: Environment, instance_id: str = ""):
    """Create an environment cli plugin."""
    return EnvironmentCliPlugin(environment, instance_id)


METTA_PLUGIN_ID_CLI_FIXTURES = "fixtures_cli"
""" cli plugin_id for the fixtures plugin """


@Factory(plugin_id=METTA_PLUGIN_ID_CLI_FIXTURES, interfaces=[METTA_PLUGIN_INTERFACE_ROLE_CLI])
def metta_plugin_factory_cli_fixtures(environment: Environment, instance_id: str = ""):
    """Create a fixtures cli plugin."""
    return FixturesCliPlugin(environment, instance_id)


METTA_PLUGIN_ID_CLI_PROVISIONER = "provisioner_cli"
""" cli plugin_id for the provisioner plugin """


@Factory(
    plugin_id=METTA_PLUGIN_ID_CLI_PROVISIONER,
    interfaces=[METTA_PLUGIN_INTERFACE_ROLE_CLI],
)
def metta_plugin_factory_provisioner_config(environment: Environment, instance_id: str = ""):
    """Create a provisioner cli plugin."""
    return ProvisionerCliPlugin(environment, instance_id)


METTA_PLUGIN_ID_CLI_OUTPUT = "output_cli"
""" cli plugin_id for the output plugin """


@Factory(
    plugin_id=METTA_PLUGIN_ID_CLI_OUTPUT,
    interfaces=[METTA_PLUGIN_INTERFACE_ROLE_CLI],
)
def metta_plugin_factory_output_config(environment: Environment, instance_id: str = ""):
    """Create a output cli plugin."""
    return OutputCliPlugin(environment, instance_id)


# ----- SetupTools EntryPoint BootStrapping ------


# pylint: disable=unused-argument
def bootstrap_environment(environment: Environment):
    """METTA_Terraform bootstrap.

    Currently we only use this to import plugins.

    Parameters:
    -----------
    env (Environment) : an environment which should have validation config added to.

    """
