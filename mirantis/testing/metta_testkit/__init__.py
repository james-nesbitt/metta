from typing import Any

from mirantis.testing.metta.plugin import Factory, Type
from mirantis.testing.metta.environment import Environment

from .provisioner import TestkitProvisionerPlugin, METTA_PLUGIN_ID_TESTKIT_PROVISIONER, TESTKIT_PROVISIONER_CONFIG_LABEL, TESTKIT_PROVISIONER_CONFIG_BASE
from .cli import TestkitCliPlugin, METTA_PLUGIN_ID_TESTKIT_CLI


@Factory(type=Type.PROVISIONER,
         plugin_id=METTA_PLUGIN_ID_TESTKIT_PROVISIONER)
def metta_plugin_factory_provisioner_testkit(environment: Environment, instance_id: str = '', label: str = TESTKIT_PROVISIONER_CONFIG_LABEL, base: Any = TESTKIT_PROVISIONER_CONFIG_BASE):
    """ create an metta litmuschaos workload plugin """
    return TestkitProvisionerPlugin(
        environment, instance_id, label=label, base=base)


@Factory(type=Type.CLI, plugin_id=METTA_PLUGIN_ID_TESTKIT_CLI)
def metta_plugin_factory_cli_testkit(environment: Environment, instance_id: str = ''):
    """ create an litmuschaos cli plugin """
    return TestkitCliPlugin(environment, instance_id)


""" SetupTools EntryPoint METTA BootStrapping """


def bootstrap(environment: Environment):
    """ METTA_testkit bootstrap

    Currently we only use this to import plugins.

    Parameters:
    -----------

    env (Environment) : an environment which should have validation config added
        to.

    """
    pass
