"""

metta Terraform

metta contrib functionality for terraform.  Primarily a terraform provisioner
plugin.

"""
from typing import Any

from configerus.loaded import LOADED_KEY_ROOT
from configerus.contrib.dict import PLUGIN_ID_SOURCE_DICT

from mirantis.testing.metta.plugin import Factory, Type
from mirantis.testing.metta.environment import Environment

from .cli import TerraformCliPlugin
from .provisioner import TerraformProvisionerPlugin, TERRAFORM_PROVISIONER_CONFIG_LABEL, TERRAFORM_VALIDATE_JSONSCHEMA

METTA_TERRAFORM_PROVISIONER_PLUGIN_ID = 'metta_terraform'
""" Terraform provisioner plugin id """


@Factory(type=Type.PROVISIONER, plugin_id=METTA_TERRAFORM_PROVISIONER_PLUGIN_ID)
def metta_plugin_factory_provisioner_terraform(
        environment: Environment, instance_id: str = "", label: str = TERRAFORM_PROVISIONER_CONFIG_LABEL, base: Any = LOADED_KEY_ROOT):
    """ create an metta provisionersss dict plugin """
    return TerraformProvisionerPlugin(environment, instance_id, label, base)


METTA_TERRAFORM_CLI_PLUGIN_ID = 'metta_terraform'
""" cli plugin_id for the info plugin """


@Factory(type=Type.CLI, plugin_id=METTA_TERRAFORM_CLI_PLUGIN_ID)
def metta_terraform_factory_cli_terraform(
        environment: Environment, instance_id: str = ''):
    """ create an info cli plugin """
    return TerraformCliPlugin(environment, instance_id)


""" SetupTools EntryPoint METTA BootStrapping """


def bootstrap(environment: Environment):
    """ METTA_Terraform bootstrap

    Currently we only use this to import plugins.

    Parameters:
    -----------

    env (Environment) : an environment which should have validation config added
        to.

    """
    pass
