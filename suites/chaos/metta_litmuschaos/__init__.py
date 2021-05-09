from typing import Any

from mirantis.testing.metta.plugin import Factory, Type
from mirantis.testing.metta.environment import Environment

from .litmuschaos_workload import LitmusChaosWorkloadPlugin, METTA_PLUGIN_ID_LITMUSCHAOS_WORKLOAD, LITMUSCHAOS_WORKLOAD_CONFIG_LABEL, LITMUSCHAOS_WORKLOAD_CONFIG_BASE
from .cli import LitmusChaosCliPlugin, METTA_PLUGIN_ID_LITMUSCHAOS_cli


@Factory(type=Type.WORKLOAD,
         plugin_id=METTA_PLUGIN_ID_LITMUSCHAOS_WORKLOAD)
def metta_plugin_factory_workload_litmuschaos(environment: Environment, instance_id: str = '',
                                              label: str = LITMUSCHAOS_WORKLOAD_CONFIG_LABEL, base: Any = LITMUSCHAOS_WORKLOAD_CONFIG_BASE):
    """ create an metta litmuschaos workload plugin """
    return LitmusChaosWorkloadPlugin(
        environment, instance_id, label=label, base=base)


@Factory(type=Type.CLI, plugin_id=METTA_PLUGIN_ID_LITMUSCHAOS_cli)
def metta_plugin_factory_cli_litmuschaos(
        environment: Environment, instance_id: str = ''):
    """ create an litmuschaos cli plugin """
    return LitmusChaosCliPlugin(environment, instance_id)
