"""

Ansible provisioner

"""

from typing import Any

from configerus.loaded import LOADED_KEY_ROOT

from mirantis.testing.metta.plugin import Factory
from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.provisioner import METTA_PLUGIN_INTERFACE_ROLE_PROVISIONER
from mirantis.testing.metta_cli.base import METTA_PLUGIN_INTERFACE_ROLE_CLI

from .provisioner import (
    AnsibleProvisionerPlugin,
    METTA_ANSIBLE_PROVISIONER_PLUGIN_ID,
    ANSIBLE_PROVISIONER_CONFIG_LABEL,
)
from .cli import AnsibleCliPlugin, METTA_ANSIBLE_CLI_PLUGIN_ID


@Factory(
    plugin_id=METTA_ANSIBLE_PROVISIONER_PLUGIN_ID,
    interfaces=[
        METTA_PLUGIN_INTERFACE_ROLE_PROVISIONER,
        METTA_ANSIBLE_PROVISIONER_PLUGIN_ID,
    ],
)
def metta_plugin_factory_provisioner_ansible(
    environment: Environment,
    instance_id: str = "",
    label: str = ANSIBLE_PROVISIONER_CONFIG_LABEL,
    base: Any = LOADED_KEY_ROOT,
):
    """create an metta provisionersss dict plugin"""
    return AnsibleProvisionerPlugin(environment, instance_id, label, base)


@Factory(
    plugin_id=METTA_ANSIBLE_CLI_PLUGIN_ID, interfaces=[METTA_PLUGIN_INTERFACE_ROLE_CLI]
)
def metta_ansible_factory_cli_ansible(environment: Environment, instance_id: str = ""):
    """create an info cli plugin"""
    return AnsibleCliPlugin(environment, instance_id)


# ----- SetupTools EntryPoint METTA BootStrapping -----


# pylint: disable=unused-argument
def bootstrap(environment: Environment):
    """METTA_Terraform bootstrap

    Currently we only use this to import plugins.

    Parameters:
    -----------

    env (Environment) : an environment which should have validation config added to.

    """
