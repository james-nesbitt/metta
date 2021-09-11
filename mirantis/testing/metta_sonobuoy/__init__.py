"""

Metta Sonobuoy package.

Primarily we register the metta plugins

"""
from typing import Any, List

from mirantis.testing.metta.plugin import Factory
from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.client import METTA_PLUGIN_INTERFACE_ROLE_CLIENT
from mirantis.testing.metta_health.healthcheck import METTA_PLUGIN_INTERFACE_ROLE_HEALTHCHECK
from mirantis.testing.metta.workload import METTA_PLUGIN_INTERFACE_ROLE_WORKLOAD
from mirantis.testing.metta_cli.base import METTA_PLUGIN_INTERFACE_ROLE_CLI

from mirantis.testing.metta_kubernetes.kubeapi_client import KubernetesApiClientPlugin

from .workload import (
    SonobuoyWorkloadPlugin,
    METTA_SONOBUOY_WORKLOAD_PLUGIN_ID,
    SONOBUOY_WORKLOAD_CONFIG_LABEL,
    SONOBUOY_WORKLOAD_CONFIG_BASE,
)
from .plugin import Plugin
from .client import SonobuoyClientPlugin, METTA_SONOBUOY_CLIENT_PLUGIN_ID
from .sonobuoy import SONOBUOY_DEFAULT_RESULTS_PATH
from .cli import SonobuoyCliPlugin, METTA_PLUGIN_ID_SONOBUOY_CLI


@Factory(
    plugin_id=METTA_SONOBUOY_WORKLOAD_PLUGIN_ID,
    interfaces=[
        METTA_PLUGIN_INTERFACE_ROLE_WORKLOAD,
        METTA_SONOBUOY_WORKLOAD_PLUGIN_ID,
    ],
)
def metta_plugin_factory_workload_sonobuoy(
    environment: Environment,
    instance_id: str = "",
    label: str = SONOBUOY_WORKLOAD_CONFIG_LABEL,
    base: Any = SONOBUOY_WORKLOAD_CONFIG_BASE,
):
    """Create a metta sonobuoy workload plugin."""
    return SonobuoyWorkloadPlugin(environment, instance_id, label=label, base=base)


@Factory(
    plugin_id=METTA_SONOBUOY_CLIENT_PLUGIN_ID,
    interfaces=[
        METTA_PLUGIN_INTERFACE_ROLE_CLIENT,
        METTA_SONOBUOY_CLIENT_PLUGIN_ID,
        METTA_PLUGIN_INTERFACE_ROLE_HEALTHCHECK,
    ],
)
# pylint: disable=too-many-arguments
def metta_plugin_factory_client_sonobuoy(
    environment: Environment,
    instance_id: str,
    kubeclient: KubernetesApiClientPlugin,
    plugins: List[Plugin] = None,
    results_path: str = SONOBUOY_DEFAULT_RESULTS_PATH,
) -> SonobuoyClientPlugin:
    """Create a metta client plugin."""
    return SonobuoyClientPlugin(
        environment,
        instance_id,
        kubeclient=kubeclient,
        plugins=plugins,
        results_path=results_path,
    )


@Factory(
    plugin_id=METTA_PLUGIN_ID_SONOBUOY_CLI,
    interfaces=[METTA_PLUGIN_INTERFACE_ROLE_CLI],
)
def metta_plugin_factory_cli_sonobuoy(environment: Environment, instance_id: str = ""):
    """Create a sonobuoy cli plugin."""
    return SonobuoyCliPlugin(environment, instance_id)


# ----- SetupTools EntryPoint METTA BootStrapping -----


# pylint: disable=unused-argument
def bootstrap_environment(environment: Environment):
    """METTA_Terraform bootstrap.

    Currently we only use this to import plugins.

    Parameters:
    -----------
    env (Environment) : an environment which should have validation config added to.

    """
