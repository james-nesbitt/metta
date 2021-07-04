"""

Metta testkit functionality.

this module registers the testkit metta plugin factories to make them available
for use.

"""
from typing import Any

from mirantis.testing.metta.plugin import Factory
from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.provisioner import METTA_PLUGIN_INTERFACE_ROLE_PROVISIONER
from mirantis.testing.metta_cli.base import METTA_PLUGIN_INTERFACE_ROLE_CLI

from .provisioner import (
    TestkitProvisionerPlugin,
    METTA_PLUGIN_ID_TESTKIT_PROVISIONER,
    TESTKIT_PROVISIONER_CONFIG_LABEL,
    TESTKIT_PROVISIONER_CONFIG_BASE,
)
from .cli import TestkitCliPlugin, METTA_PLUGIN_ID_TESTKIT_CLI


@Factory(
    plugin_id=METTA_PLUGIN_ID_TESTKIT_PROVISIONER,
    interfaces=[
        METTA_PLUGIN_INTERFACE_ROLE_PROVISIONER,
        METTA_PLUGIN_ID_TESTKIT_PROVISIONER,
    ],
)
def metta_plugin_factory_provisioner_testkit(
    environment: Environment,
    instance_id: str = "",
    label: str = TESTKIT_PROVISIONER_CONFIG_LABEL,
    base: Any = TESTKIT_PROVISIONER_CONFIG_BASE,
):
    """Create an metta litmuschaos workload plugin."""
    return TestkitProvisionerPlugin(environment, instance_id, label=label, base=base)


@Factory(
    plugin_id=METTA_PLUGIN_ID_TESTKIT_CLI,
    interfaces=[METTA_PLUGIN_INTERFACE_ROLE_CLI],
)
def metta_plugin_factory_cli_testkit(environment: Environment, instance_id: str = ""):
    """Create an litmuschaos cli plugin."""
    return TestkitCliPlugin(environment, instance_id)


# ----- SetupTools EntryPoint METTA BootStrapping -----


# pylint: disable=unused-argument
def bootstrap(environment):
    """METTA_testkit bootstrap.

    Currently we only use this to import plugins.

    Parameters:
    -----------
    env (Environment) : an environment

    """
