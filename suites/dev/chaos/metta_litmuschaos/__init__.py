"""
METTA CONTRIB: litmus chaos integration package

This package contains workload and cli plugins for litmus chaos integration into metta.

"""
from typing import Any

from mirantis.testing.metta.plugin import Factory
from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.workload import METTA_PLUGIN_INTERFACE_ROLE_WORKLOAD
from mirantis.testing.metta_cli.base import METTA_PLUGIN_INTERFACE_ROLE_CLI

from .litmuschaos_workload import (
    LitmusChaosWorkloadPlugin,
    METTA_PLUGIN_ID_LITMUSCHAOS_WORKLOAD,
    LITMUSCHAOS_WORKLOAD_CONFIG_LABEL,
    LITMUSCHAOS_WORKLOAD_CONFIG_BASE,
)
from .cli import LitmusChaosCliPlugin, METTA_PLUGIN_ID_LITMUSCHAOS_CLI


@Factory(
    plugin_type=METTA_PLUGIN_INTERFACE_ROLE_WORKLOAD,
    plugin_id=METTA_PLUGIN_ID_LITMUSCHAOS_WORKLOAD,
)
def metta_plugin_factory_workload_litmuschaos(
    environment: Environment,
    instance_id: str = "",
    label: str = LITMUSCHAOS_WORKLOAD_CONFIG_LABEL,
    base: Any = LITMUSCHAOS_WORKLOAD_CONFIG_BASE,
):
    """create an metta litmuschaos workload plugin"""
    return LitmusChaosWorkloadPlugin(environment, instance_id, label=label, base=base)


@Factory(
    plugin_type=METTA_PLUGIN_INTERFACE_ROLE_CLI,
    plugin_id=METTA_PLUGIN_ID_LITMUSCHAOS_CLI,
)
def metta_plugin_factory_cli_litmuschaos(
    environment: Environment, instance_id: str = ""
):
    """create an litmuschaos cli plugin"""
    return LitmusChaosCliPlugin(environment, instance_id)
