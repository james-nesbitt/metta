"""

Metta contrib package for using Mirantis launchpad to provision clusters.

This allows using launchpad to install the Mirantis products onto a cluster
that had already been provisioned by other services.

This module registers the package metta plugins.

"""
from typing import Any, Dict

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
from .client import METTA_LAUNCHPAD_CLIENT_PLUGIN_ID, LaunchpadClientPlugin
from .cli import (
    LaunchpadCliPlugin,
    METTA_LAUNCHPAD_CLI_PLUGIN_ID,
)
from .launchpad import (
    METTA_LAUNCHPAD_CLI_CONFIG_FILE_DEFAULT,
    METTA_LAUNCHPADCLIENT_WORKING_DIR_DEFAULT,
)


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
    plugin_id=METTA_LAUNCHPAD_CLIENT_PLUGIN_ID,
    interfaces=[METTA_PLUGIN_INTERFACE_ROLE_CLIENT],
)
# pylint: disable=too-many-arguments
def metta_terraform_factory_client_launchpad(
    environment: Environment,
    instance_id: str = "",
    config_file: str = METTA_LAUNCHPAD_CLI_CONFIG_FILE_DEFAULT,
    working_dir: str = METTA_LAUNCHPADCLIENT_WORKING_DIR_DEFAULT,
    cli_options: Dict[str, Any] = None,
    systems: Dict[str, Dict[str, str]] = None,
):
    """Create a launchpad client plugin."""
    return LaunchpadClientPlugin(
        environment=environment,
        instance_id=instance_id,
        config_file=config_file,
        working_dir=working_dir,
        cli_options=cli_options,
        systems=systems,
    )


@Factory(
    plugin_id=METTA_LAUNCHPAD_CLI_PLUGIN_ID,
    interfaces=[METTA_PLUGIN_INTERFACE_ROLE_CLI],
)
def metta_terraform_factory_cli_launchpad(environment: Environment, instance_id: str = ""):
    """Create a launchpad cli plugin."""
    return LaunchpadCliPlugin(environment, instance_id)


# ----- METTA BOOTSTRAPPERS -----


# pylint: disable=unused-argument
def bootstrap_environment(environment: Environment):
    """METTA_Terraform bootstrap.

    Currently we only use this to import plugins.

    Parameters:
    -----------
    env (Environment) : an environment which should have validation config added to.

    """
