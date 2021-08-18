"""

Ansible provisioner

"""

from typing import Any

from configerus.loaded import LOADED_KEY_ROOT

from mirantis.testing.metta.plugin import Factory
from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.provisioner import METTA_PLUGIN_INTERFACE_ROLE_PROVISIONER
from mirantis.testing.metta.client import METTA_PLUGIN_INTERFACE_ROLE_CLIENT
from mirantis.testing.metta.workload import METTA_PLUGIN_INTERFACE_ROLE_WORKLOAD
from mirantis.testing.metta_health.healthcheck import METTA_PLUGIN_INTERFACE_ROLE_HEALTHCHECK
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
from .ansiblecli_workload import (
    AnsibleCliCoreWorkloadPlugin,
    AnsibleCliPlaybookWorkloadPlugin,
    METTA_ANSIBLE_ANSIBLECLI_COREWORKLOAD_PLUGIN_ID,
    METTA_ANSIBLE_ANSIBLECLI_PLAYBOOKWORKLOAD_PLUGIN_ID,
    ANSIBLE_WORKLOAD_CONFIG_LABEL,
)
from .cli import AnsibleCliPlugin, METTA_ANSIBLE_CLI_PLUGIN_ID


@Factory(
    plugin_id=METTA_ANSIBLE_ANSIBLECLIPLAYBOOK_PROVISIONER_PLUGIN_ID,
    interfaces=[METTA_PLUGIN_INTERFACE_ROLE_PROVISIONER],
)
def metta_plugin_factory_provisioner_ansibleplaybook(
    environment: Environment,
    instance_id: str = "",
    label: str = ANSIBLE_PROVISIONER_CONFIG_LABEL,
    base: Any = LOADED_KEY_ROOT,
):
    """create a metta provisioner plugin"""
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
    """create a metta client plugin"""
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
    """create a metta client plugin"""
    return AnsiblePlaybookClientPlugin(
        environment, instance_id, inventory_path=inventory_path, ansiblecfg_path=ansiblecfg_path
    )


@Factory(
    plugin_id=METTA_ANSIBLE_ANSIBLECLI_COREWORKLOAD_PLUGIN_ID,
    interfaces=[METTA_PLUGIN_INTERFACE_ROLE_WORKLOAD],
)
def metta_plugin_factory_coreworkload_ansible(
    environment: Environment,
    instance_id: str = "",
    label: str = ANSIBLE_WORKLOAD_CONFIG_LABEL,
    base: Any = LOADED_KEY_ROOT,
):
    """create a metta workload plugin"""
    return AnsibleCliCoreWorkloadPlugin(environment, instance_id, label, base)


@Factory(
    plugin_id=METTA_ANSIBLE_ANSIBLECLI_PLAYBOOKWORKLOAD_PLUGIN_ID,
    interfaces=[METTA_PLUGIN_INTERFACE_ROLE_WORKLOAD],
)
def metta_plugin_factory_playbookworkload_ansible(
    environment: Environment,
    instance_id: str = "",
    label: str = ANSIBLE_WORKLOAD_CONFIG_LABEL,
    base: Any = LOADED_KEY_ROOT,
):
    """create a metta workload plugin"""
    return AnsibleCliPlaybookWorkloadPlugin(environment, instance_id, label, base)


@Factory(plugin_id=METTA_ANSIBLE_CLI_PLUGIN_ID, interfaces=[METTA_PLUGIN_INTERFACE_ROLE_CLI])
def metta_ansible_factory_cli_ansible(environment: Environment, instance_id: str = ""):
    """create a ansible cli plugin"""
    return AnsibleCliPlugin(environment, instance_id)


# ----- SetupTools EntryPoint METTA BootStrapping -----


# pylint: disable=unused-argument
def bootstrap_environment(environment: Environment):
    """METTA_Terraform bootstrap

    Currently we only use this to import plugins.

    Parameters:
    -----------

    env (Environment) : an environment which should have validation config added to.

    """
