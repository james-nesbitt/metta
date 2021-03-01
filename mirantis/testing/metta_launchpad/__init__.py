
from typing import Any

from configerus.loaded import LOADED_KEY_ROOT
from configerus.contrib.dict import PLUGIN_ID_SOURCE_DICT

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.plugin import Factory as Factory, Type as Type

from .launchpad import LaunchpadClient
from .provisioner import LaunchpadProvisionerPlugin, METTA_LAUNCHPAD_CONFIG_LABEL, METTA_LAUNCHPAD_VALIDATE_JSONSCHEMA
from .exec_client import LaunchpadExecClientPlugin, METTA_LAUNCHPAD_EXEC_CLIENT_PLUGIN_ID as EXEC_CLIENT_PLUGIN_ID
from .cli import LaunchpadCliPlugin

""" GENERATING CONFIG  """

METTA_LAUNCHPAD_PROVISIONER_PLUGIN_ID = "metta_launchpad"
METTA_LAUNCHPAD_CLI_PLUGIN_ID = "metta_launchpad"
METTA_LAUNCHPAD_EXEC_CLIENT_PLUGIN_ID = EXEC_CLIENT_PLUGIN_ID

""" provisioner plugin_id for the plugin """


@Factory(type=Type.PROVISIONER,
         plugin_id=METTA_LAUNCHPAD_PROVISIONER_PLUGIN_ID)
def metta_plugin_factory_provisioner_launchpad(
        environment: Environment, instance_id: str = "", label: str = METTA_LAUNCHPAD_CONFIG_LABEL, base: Any = LOADED_KEY_ROOT):
    """ create a launchpad provisioner plugin """
    return LaunchpadProvisionerPlugin(environment, instance_id, label, base)


@Factory(type=Type.CLIENT, plugin_id=METTA_LAUNCHPAD_EXEC_CLIENT_PLUGIN_ID)
def metta_terraform_factory_cliexec_client_launchpad(
        environment: Environment, instance_id: str = '', client: LaunchpadClient = None):
    """ create an launchpad exec client plugin """
    return LaunchpadExecClientPlugin(environment, instance_id, client)


@Factory(type=Type.CLI, plugin_id=METTA_LAUNCHPAD_CLI_PLUGIN_ID)
def metta_terraform_factory_cli_launchpad(
        environment: Environment, instance_id: str = ''):
    """ create an launchpad cli plugin """
    return LaunchpadCliPlugin(environment, instance_id)


""" METTA BOOTSTRAPPERS """


def bootstrap(environment: Environment):
    """ metta configerus bootstrap

    Currently we only use this to import plugins.

    Parameters:
    -----------

    env (Environment) : an environment which should have validation config added
        to.

    """
    pass
