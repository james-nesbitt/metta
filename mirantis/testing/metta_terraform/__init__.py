"""

Metta Terraform.

metta contrib functionality for terraform.  Primarily a terraform provisioner
plugin.

"""
from typing import Any

from configerus.loaded import LOADED_KEY_ROOT

from mirantis.testing.metta.plugin import Factory
from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.provisioner import METTA_PLUGIN_TYPE_PROVISIONER
from mirantis.testing.metta_cli.base import METTA_PLUGIN_TYPE_CLI

from .cli import TerraformCliPlugin, METTA_TERRAFORM_CLI_PLUGIN_ID
from .provisioner import (TerraformProvisionerPlugin, TERRAFORM_PROVISIONER_CONFIG_LABEL,
                          METTA_TERRAFORM_PROVISIONER_PLUGIN_ID)


@Factory(plugin_type=METTA_PLUGIN_TYPE_PROVISIONER, plugin_id=METTA_TERRAFORM_PROVISIONER_PLUGIN_ID)
def metta_plugin_factory_provisioner_terraform(environment: Environment, instance_id: str = "",
                                               label: str = TERRAFORM_PROVISIONER_CONFIG_LABEL,
                                               base: Any = LOADED_KEY_ROOT):
    """Create an metta provisionersss dict plugin."""
    return TerraformProvisionerPlugin(environment, instance_id, label, base)


@Factory(plugin_type=METTA_PLUGIN_TYPE_CLI, plugin_id=METTA_TERRAFORM_CLI_PLUGIN_ID)
def metta_terraform_factory_cli_terraform(environment: Environment, instance_id: str = ''):
    """Create an info cli plugin."""
    return TerraformCliPlugin(environment, instance_id)


# ----- SetupTools EntryPoint METTA BootStrapping -----


# pylint: disable=unused-argument
def bootstrap(environment: Environment):
    """METTA_Terraform bootstrap.

    Currently we only use this to import plugins.

    Parameters:
    -----------
    env (Environment) : an environment which should have validation config added.

    """
