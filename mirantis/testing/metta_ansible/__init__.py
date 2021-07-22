"""

Ansible provisioner

"""

from typing import Any

from configerus.loaded import LOADED_KEY_ROOT

from mirantis.testing.metta.plugin import Factory
from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.provisioner import METTA_PLUGIN_INTERFACE_ROLE_PROVISIONER
from mirantis.testing.metta.client import METTA_PLUGIN_INTERFACE_ROLE_CLIENT
from mirantis.testing.metta.healthcheck import METTA_PLUGIN_INTERFACE_ROLE_HEALTHCHECK
from mirantis.testing.metta_cli.base import METTA_PLUGIN_INTERFACE_ROLE_CLI

from .ansiblecli_provisioner import (
    AnsiblePlaybookProvisionerPlugin,
    METTA_ANSIBLE_ANSIBLECLIPLAYBOOK_PROVISIONER_PLUGIN_ID,
    ANSIBLE_PROVISIONER_CONFIG_LABEL,
)
from .ansiblecli_client import (
    AnsibleClientPlugin,
    AnsiblePlaybookClientPlugin,
    METTA_ANSIBLE_ANSIBLECLI_CORECLIENT_PLUGIN_ID,
    METTA_ANSIBLE_ANSIBLECLI_PLAYBOOKCLIENT_PLUGIN_ID,
)
from .cli import AnsibleCliPlugin, METTA_ANSIBLE_CLI_PLUGIN_ID


@Factory(
    plugin_id=METTA_ANSIBLE_ANSIBLECLIPLAYBOOK_PROVISIONER_PLUGIN_ID,
    interfaces=[
        METTA_PLUGIN_INTERFACE_ROLE_PROVISIONER,
    ],
)
def metta_plugin_factory_provisioner_ansibleplaybook(
    environment: Environment,
    instance_id: str = "",
    label: str = ANSIBLE_PROVISIONER_CONFIG_LABEL,
    base: Any = LOADED_KEY_ROOT,
):
    """create an metta provisioners plugin"""
    return AnsiblePlaybookProvisionerPlugin(environment, instance_id, label, base)


@Factory(
    plugin_id=METTA_ANSIBLE_ANSIBLECLI_CORECLIENT_PLUGIN_ID,
    interfaces=[METTA_PLUGIN_INTERFACE_ROLE_CLIENT, METTA_PLUGIN_INTERFACE_ROLE_HEALTHCHECK],
)
def metta_plugin_factory_client_ansibleplaybook(
    environment: Environment,
    instance_id: str = "",
    inventory_path: str = "",
    ansiblecfg_path: str = "",
):
    """create an metta client plugin"""
    return AnsibleClientPlugin(
        environment, instance_id, inventory_path=inventory_path, ansiblecfg_path=ansiblecfg_path
    )


@Factory(
    plugin_id=METTA_ANSIBLE_ANSIBLECLI_PLAYBOOKCLIENT_PLUGIN_ID,
    interfaces=[METTA_PLUGIN_INTERFACE_ROLE_CLIENT],
)
def metta_plugin_factory_client_ansible(
    environment: Environment,
    instance_id: str = "",
    inventory_path: str = "",
    ansiblecfg_path: str = "",
):
    """create an metta client plugin"""
    return AnsiblePlaybookClientPlugin(
        environment, instance_id, inventory_path=inventory_path, ansiblecfg_path=ansiblecfg_path
    )


@Factory(plugin_id=METTA_ANSIBLE_CLI_PLUGIN_ID, interfaces=[METTA_PLUGIN_INTERFACE_ROLE_CLI])
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
