"""

Metta plugin importing and configuration for k0s.

Primarily used to register plugins.

"""
from typing import Dict, Any

from configerus.loaded import LOADED_KEY_ROOT

from mirantis.testing.metta.plugin import Factory
from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.client import METTA_PLUGIN_INTERFACE_ROLE_CLIENT
from mirantis.testing.metta_cli.base import METTA_PLUGIN_INTERFACE_ROLE_CLI

from .cli import K0sCliPlugin, METTA_K0S_CLI_PLUGIN_ID
from .k0sctl_client import K0sctlClientPlugin, METTA_K0S_K0SCTL_CLIENT_PLUGIN_ID


@Factory(
    plugin_id=METTA_K0S_K0SCTL_CLIENT_PLUGIN_ID,
    interfaces=[
        METTA_PLUGIN_INTERFACE_ROLE_CLIENT,
        METTA_K0S_K0SCTL_CLIENT_PLUGIN_ID,
    ],
)
# pylint: disable=too-many-arguments
def metta_plugin_factory_client_k0sctl(
    environment: Environment, instance_id: str
) -> K0sctlClientPlugin:
    """Create an metta client plugin."""
    return K0sctlClientPlugin(environment, instance_id)


@Factory(
    plugin_id=METTA_K0S_CLI_PLUGIN_ID,
    interfaces=[METTA_PLUGIN_INTERFACE_ROLE_CLI],
)
def metta_terraform_factory_cli_terraform(
    environment: Environment, instance_id: str
) -> K0sCliPlugin:
    """Create a cli plugin."""
    return K0sCliPlugin(environment, instance_id)


# ----- SetupTools EntryPoint METTA BootStrapping -----


# pylint: disable=unused-argument
def bootstrap_environment(environment: Environment):
    """METTA K0S bootstrap.

    Currently we only use this to import plugins.

    Parameters:
    -----------
    env (Environment) : an environment which should have validation config added.

    """
