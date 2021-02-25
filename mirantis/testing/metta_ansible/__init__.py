"""

Ansible provisioner

"""

from typing import Any

from configerus.loaded import LOADED_KEY_ROOT

from mirantis.testing.metta.plugin import Factory, Type
from mirantis.testing.metta.environment import Environment

from .provisioner import AnsibleProvisionerPlugin, ANSIBLE_PROVISIONER_CONFIG_LABEL
from .cli import AnsibleCliPlugin

METTA_ANSIBLE_PROVISIONER_PLUGIN_ID = 'metta_ansible'
""" Ansible provisioner plugin id """


@Factory(type=Type.PROVISIONER, plugin_id=METTA_ANSIBLE_PROVISIONER_PLUGIN_ID)
def metta_plugin_factory_provisioner_ansible(
        environment: Environment, instance_id: str = "", label: str = ANSIBLE_PROVISIONER_CONFIG_LABEL, base: Any = LOADED_KEY_ROOT):
    """ create an metta provisionersss dict plugin """
    return AnsibleProvisionerPlugin(environment, instance_id, label, base)


METTA_ANSIBLE_CLI_PLUGIN_ID = 'metta_ansible'
""" cli plugin_id for the info plugin """


@Factory(type=Type.CLI, plugin_id=METTA_ANSIBLE_CLI_PLUGIN_ID)
def metta_ansible_factory_cli_ansible(
        environment: Environment, instance_id: str = ''):
    """ create an info cli plugin """
    return AnsibleCliPlugin(environment, instance_id)


""" SetupTools EntryPoint METTA BootStrapping """


def bootstrap(environment: Environment):
    """ METTA_Ansible bootstrap

    We dont't take any action.  Our purpose is to run the above factory
    decorator to register our plugin.

    """
    pass
