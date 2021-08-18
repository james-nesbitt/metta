"""

Metta testkit functionality.

this module registers the testkit metta plugin factories to make them available
for use.

"""
from typing import Any, Dict

from mirantis.testing.metta.plugin import Factory
from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.provisioner import METTA_PLUGIN_INTERFACE_ROLE_PROVISIONER
from mirantis.testing.metta.client import METTA_PLUGIN_INTERFACE_ROLE_CLIENT
from mirantis.testing.metta_cli.base import METTA_PLUGIN_INTERFACE_ROLE_CLI

from .provisioner import (
    TestkitProvisionerPlugin,
    METTA_TESTKIT_PROVISIONER_PLUGIN_ID,
    TESTKIT_PROVISIONER_CONFIG_LABEL,
    TESTKIT_PROVISIONER_CONFIG_BASE,
)
from .client import (
    TestkitClientPlugin,
    METTA_TESTKIT_CLIENT_PLUGIN_ID,
)
from .cli import TestkitCliPlugin, METTA_TESTKIT_CLI_PLUGIN_ID


@Factory(
    plugin_id=METTA_TESTKIT_PROVISIONER_PLUGIN_ID,
    interfaces=[
        METTA_PLUGIN_INTERFACE_ROLE_PROVISIONER,
        METTA_TESTKIT_PROVISIONER_PLUGIN_ID,
    ],
)
def metta_plugin_factory_provisioner_testkit(
    environment: Environment,
    instance_id: str,
    label: str = TESTKIT_PROVISIONER_CONFIG_LABEL,
    base: Any = TESTKIT_PROVISIONER_CONFIG_BASE,
) -> TestkitProvisionerPlugin:
    """Create an metta testkit provisioner plugin."""
    return TestkitProvisionerPlugin(environment, instance_id, label=label, base=base)


@Factory(
    plugin_id=METTA_TESTKIT_CLIENT_PLUGIN_ID,
    interfaces=[
        METTA_PLUGIN_INTERFACE_ROLE_CLIENT,
        METTA_TESTKIT_CLIENT_PLUGIN_ID,
    ],
)
def metta_plugin_factory_client_testkit(
    environment: Environment,
    instance_id: str,
    system_name: str,
    config_file: str,
    systems: Dict[str, Dict[str, str]] = None,
) -> TestkitClientPlugin:
    """Create an metta testkit client plugin."""
    return TestkitClientPlugin(
        environment, instance_id, system_name=system_name, config_file=config_file, systems=systems
    )


@Factory(
    plugin_id=METTA_TESTKIT_CLI_PLUGIN_ID,
    interfaces=[METTA_PLUGIN_INTERFACE_ROLE_CLI],
)
def metta_plugin_factory_cli_testkit(
    environment: Environment, instance_id: str = ""
) -> TestkitCliPlugin:
    """Create an litmuschaos cli plugin."""
    return TestkitCliPlugin(environment, instance_id)


# ----- SetupTools EntryPoint METTA BootStrapping -----


# pylint: disable=unused-argument
def bootstrap_environment(environment):
    """METTA_testkit bootstrap.

    Currently we only use this to import plugins.

    Parameters:
    -----------
    env (Environment) : an environment

    """
