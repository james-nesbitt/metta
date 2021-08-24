"""

Metta Terraform.

metta contrib functionality for terraform.  Primarily a terraform provisioner
plugin.

"""
from typing import Dict, Any

from configerus.loaded import LOADED_KEY_ROOT

from mirantis.testing.metta.plugin import Factory
from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.provisioner import METTA_PLUGIN_INTERFACE_ROLE_PROVISIONER
from mirantis.testing.metta.client import METTA_PLUGIN_INTERFACE_ROLE_CLIENT
from mirantis.testing.metta_cli.base import METTA_PLUGIN_INTERFACE_ROLE_CLI

from .cli import TerraformCliPlugin, METTA_TERRAFORM_CLI_PLUGIN_ID
from .provisioner import (
    TerraformProvisionerPlugin,
    TERRAFORM_PROVISIONER_CONFIG_LABEL,
    METTA_TERRAFORM_PROVISIONER_PLUGIN_ID,
)
from .client import TerraformClientPlugin, METTA_TERRAFORM_CLIENT_PLUGIN_ID


@Factory(
    plugin_id=METTA_TERRAFORM_PROVISIONER_PLUGIN_ID,
    interfaces=[
        METTA_PLUGIN_INTERFACE_ROLE_PROVISIONER,
        METTA_TERRAFORM_PROVISIONER_PLUGIN_ID,
    ],
)
def metta_plugin_factory_provisioner_terraform(
    environment: Environment,
    instance_id: str,
    label: str = TERRAFORM_PROVISIONER_CONFIG_LABEL,
    base: Any = LOADED_KEY_ROOT,
) -> TerraformProvisionerPlugin:
    """Create an metta provisioners plugin."""
    return TerraformProvisionerPlugin(environment, instance_id, label, base)


@Factory(
    plugin_id=METTA_TERRAFORM_CLIENT_PLUGIN_ID,
    interfaces=[
        METTA_PLUGIN_INTERFACE_ROLE_CLIENT,
        METTA_TERRAFORM_CLIENT_PLUGIN_ID,
    ],
)
# pylint: disable=too-many-arguments
def metta_plugin_factory_client_terraform(
    environment: Environment,
    instance_id: str,
    chart_path: str,
    state_path: str,
    tfvars: Dict[str, Any],
    tfvars_path: str,
) -> TerraformClientPlugin:
    """Create an metta client plugin."""
    return TerraformClientPlugin(
        environment,
        instance_id,
        chart_path=chart_path,
        state_path=state_path,
        tfvars=tfvars,
        tfvars_path=tfvars_path,
    )


@Factory(
    plugin_id=METTA_TERRAFORM_CLI_PLUGIN_ID,
    interfaces=[METTA_PLUGIN_INTERFACE_ROLE_CLI],
)
def metta_terraform_factory_cli_terraform(
    environment: Environment, instance_id: str
) -> TerraformCliPlugin:
    """Create a cli plugin."""
    return TerraformCliPlugin(environment, instance_id)


# ----- SetupTools EntryPoint METTA BootStrapping -----


# pylint: disable=unused-argument
def bootstrap_environment(environment: Environment):
    """METTA_Terraform bootstrap.

    Currently we only use this to import plugins.

    Parameters:
    -----------
    env (Environment) : an environment which should have validation config added.

    """
