"""

Metta Sonobuoy package.

Primarily we register the metta plugins

"""
from typing import Any

from mirantis.testing.metta.plugin import Factory
from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.workload import METTA_PLUGIN_INTERFACE_ROLE_WORKLOAD
from mirantis.testing.metta_cli.base import METTA_PLUGIN_INTERFACE_ROLE_CLI

from .sonobuoy_workload import (
    SonobuoyWorkloadPlugin,
    METTA_PLUGIN_ID_SONOBUOY_WORKLOAD,
    SONOBUOY_WORKLOAD_CONFIG_LABEL,
    SONOBUOY_WORKLOAD_CONFIG_BASE,
)
from .cli import SonobuoyCliPlugin, METTA_PLUGIN_ID_SONOBUOY_CLI


@Factory(
    plugin_id=METTA_PLUGIN_ID_SONOBUOY_WORKLOAD,
    interfaces=[
        METTA_PLUGIN_INTERFACE_ROLE_WORKLOAD,
        METTA_PLUGIN_ID_SONOBUOY_WORKLOAD,
    ],
)
def metta_plugin_factory_workload_sonobuoy(
    environment: Environment,
    instance_id: str = "",
    label: str = SONOBUOY_WORKLOAD_CONFIG_LABEL,
    base: Any = SONOBUOY_WORKLOAD_CONFIG_BASE,
):
    """Create an metta sonobuoy workload plugin."""
    return SonobuoyWorkloadPlugin(environment, instance_id, label=label, base=base)


@Factory(
    plugin_id=METTA_PLUGIN_ID_SONOBUOY_CLI,
    interfaces=[METTA_PLUGIN_INTERFACE_ROLE_CLI],
)
def metta_plugin_factory_cli_sonobuoy(environment: Environment, instance_id: str = ""):
    """Create an sonobuoy cli plugin."""
    return SonobuoyCliPlugin(environment, instance_id)


# ----- SetupTools EntryPoint METTA BootStrapping -----


# pylint: disable=unused-argument
def bootstrap(environment: Environment):
    """METTA_Terraform bootstrap.

    Currently we only use this to import plugins.

    Parameters:
    -----------
    env (Environment) : an environment which should have validation config added to.

    """
