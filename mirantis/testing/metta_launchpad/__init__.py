"""

Metta contrib package for using Mirantis launchpad to provision clusters.

This allows using launchpad to install the Mirantis products onto a cluster
that had already been provisioned by other services.

This module registers the package metta plugins.

"""
from typing import Any

from configerus.loaded import LOADED_KEY_ROOT

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.plugin import Factory
from mirantis.testing.metta.provisioner import METTA_PLUGIN_INTERFACE_ROLE_PROVISIONER
from mirantis.testing.metta.client import METTA_PLUGIN_INTERFACE_ROLE_CLIENT
from mirantis.testing.metta_cli.base import METTA_PLUGIN_INTERFACE_ROLE_CLI

from .launchpad import LaunchpadClient
from .provisioner import (
    LaunchpadProvisionerPlugin,
    METTA_LAUNCHPAD_PROVISIONER_PLUGIN_ID,
    METTA_LAUNCHPAD_CONFIG_LABEL,
)
from .exec_client import (
    LaunchpadExecClientPlugin,
    METTA_LAUNCHPAD_EXEC_CLIENT_PLUGIN_ID,
)
from .cli import LaunchpadCliPlugin, METTA_LAUNCHPAD_CLI_PLUGIN_ID


@Factory(
    plugin_id=METTA_LAUNCHPAD_PROVISIONER_PLUGIN_ID,
    interfaces=[
        METTA_PLUGIN_INTERFACE_ROLE_PROVISIONER,
        METTA_LAUNCHPAD_PROVISIONER_PLUGIN_ID,
    ],
)
def metta_plugin_factory_provisioner_launchpad(
    environment: Environment,
    instance_id: str = "",
    label: str = METTA_LAUNCHPAD_CONFIG_LABEL,
    base: Any = LOADED_KEY_ROOT,
):
    """Create a launchpad provisioner plugin."""
    return LaunchpadProvisionerPlugin(environment, instance_id, label, base)


@Factory(
    plugin_id=METTA_LAUNCHPAD_EXEC_CLIENT_PLUGIN_ID,
    interfaces=[METTA_PLUGIN_INTERFACE_ROLE_CLIENT],
)
def metta_terraform_factory_cliexec_client_launchpad(
    environment: Environment, instance_id: str = "", client: LaunchpadClient = None
):
    """Create an launchpad exec client plugin."""
    return LaunchpadExecClientPlugin(environment, instance_id, client)


@Factory(
    plugin_id=METTA_LAUNCHPAD_CLI_PLUGIN_ID,
    interfaces=[METTA_PLUGIN_INTERFACE_ROLE_CLI],
)
def metta_terraform_factory_cli_launchpad(
    environment: Environment, instance_id: str = ""
):
    """Create an launchpad cli plugin."""
    return LaunchpadCliPlugin(environment, instance_id)


# ----- METTA BOOTSTRAPPERS -----


# pylint: disable=unused-argument
def bootstrap(environment: Environment):
    """METTA_Terraform bootstrap.

    Currently we only use this to import plugins.

    Parameters:
    -----------
    env (Environment) : an environment which should have validation config added to.

    """
