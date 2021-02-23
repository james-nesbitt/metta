
from typing import Any

from configerus.loaded import LOADED_KEY_ROOT

from uctt.environment import Environment
from uctt.plugin import Factory as Factory, Type as Type

from .provisioner import LaunchpadProvisionerPlugin, MTT_LAUNCHPAD_CONFIG_LABEL
from .cli import LaunchpadCliPlugin

""" GENERATING CONFIG  """

MTT_LAUNCHPAD_PROVISIONER_PLUGIN_ID = "mtt_launchpad"
MTT_LAUNCHPAD_CLI_PLUGIN_ID = "mtt_launchpad"

""" provisioner plugin_id for the plugin """


@Factory(type=Type.PROVISIONER,
         plugin_id=MTT_LAUNCHPAD_PROVISIONER_PLUGIN_ID)
def mtt_plugin_factory_provisioner_launchpad(
        environment: Environment, instance_id: str = "", label: str = MTT_LAUNCHPAD_CONFIG_LABEL, base: Any = LOADED_KEY_ROOT):
    """ create a launchpad provisioner plugin """
    return LaunchpadProvisionerPlugin(environment, instance_id, label, base)


@Factory(type=Type.CLI, plugin_id=MTT_LAUNCHPAD_CLI_PLUGIN_ID)
def uctt_terraform_factory_cli_launchpad(
        environment: Environment, instance_id: str = ''):
    """ create an launchpad cli plugin """
    return LaunchpadCliPlugin(environment, instance_id)


""" UCTT BOOTSTRAPPERS """


def uctt_bootstrap(environment: Environment):
    """ MTT configerus bootstrap

    do nothing other than include the above registration decoration

    """
    pass
