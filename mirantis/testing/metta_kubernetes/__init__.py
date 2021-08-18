"""

METTA Kubernetes.

metta contrib functionality for Kubernetes.  In particular to provide plugins
for kubernetes clients and kubernetes workloads.

"""

from typing import Any

from mirantis.testing.metta.plugin import Factory
from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.client import METTA_PLUGIN_INTERFACE_ROLE_CLIENT
from mirantis.testing.metta_health.healthcheck import METTA_PLUGIN_INTERFACE_ROLE_HEALTHCHECK
from mirantis.testing.metta.workload import METTA_PLUGIN_INTERFACE_ROLE_WORKLOAD
from mirantis.testing.metta_cli.base import METTA_PLUGIN_INTERFACE_ROLE_CLI

from .kubeapi_client import (
    KubernetesApiClientPlugin,
    METTA_PLUGIN_ID_KUBERNETES_CLIENT,
)
from .deployment_workload import (
    KubernetesDeploymentWorkloadPlugin,
    METTA_PLUGIN_ID_KUBERNETES_DEPLOYMENT_WORKLOAD,
    KUBERNETES_DEPLOYMENT_WORKLOAD_CONFIG_LABEL,
    KUBERNETES_DEPLOYMENT_WORKLOAD_CONFIG_BASE,
)
from .yaml_workload import (
    KubernetesYamlWorkloadPlugin,
    METTA_PLUGIN_ID_KUBERNETES_YAML_WORKLOAD,
    KUBERNETES_YAML_WORKLOAD_CONFIG_LABEL,
    KUBERNETES_YAML_WORKLOAD_CONFIG_BASE,
)
from .helm_workload import (
    KubernetesHelmWorkloadPlugin,
    METTA_PLUGIN_ID_KUBERNETES_HELM_WORKLOAD,
    KUBERNETES_HELM_WORKLOAD_CONFIG_LABEL,
    KUBERNETES_HELM_WORKLOAD_CONFIG_BASE,
)
from .cli import KubernetesCliPlugin, METTA_PLUGIN_ID_KUBERNETES_CLI


@Factory(
    plugin_id=METTA_PLUGIN_ID_KUBERNETES_CLIENT,
    interfaces=[
        METTA_PLUGIN_INTERFACE_ROLE_CLIENT,
        METTA_PLUGIN_INTERFACE_ROLE_HEALTHCHECK,
        METTA_PLUGIN_ID_KUBERNETES_CLIENT,
    ],
)
def metta_plugin_factory_client_kubernetes(
    environment: Environment, instance_id: str = "", kube_config_file: str = ""
) -> KubernetesApiClientPlugin:
    """Create a metta kubernetes client plugin."""
    return KubernetesApiClientPlugin(environment, instance_id, kube_config_file)


@Factory(
    plugin_id=METTA_PLUGIN_ID_KUBERNETES_DEPLOYMENT_WORKLOAD,
    interfaces=[
        METTA_PLUGIN_INTERFACE_ROLE_WORKLOAD,
        METTA_PLUGIN_INTERFACE_ROLE_HEALTHCHECK,
    ],
)
def metta_plugin_factory_workload_kubernetes_deployment(
    environment: Environment,
    instance_id: str = "",
    label: str = KUBERNETES_DEPLOYMENT_WORKLOAD_CONFIG_LABEL,
    base: Any = KUBERNETES_DEPLOYMENT_WORKLOAD_CONFIG_BASE,
):
    """Create a metta kubernetes spec workload plugin."""
    return KubernetesDeploymentWorkloadPlugin(environment, instance_id, label=label, base=base)


@Factory(
    plugin_id=METTA_PLUGIN_ID_KUBERNETES_YAML_WORKLOAD,
    interfaces=[METTA_PLUGIN_INTERFACE_ROLE_WORKLOAD],
)
def metta_plugin_factory_workload_kubernetes_yaml(
    environment: Environment,
    instance_id: str = "",
    label: str = KUBERNETES_YAML_WORKLOAD_CONFIG_LABEL,
    base: Any = KUBERNETES_YAML_WORKLOAD_CONFIG_BASE,
):
    """Create a metta kubernetes spec workload plugin."""
    return KubernetesYamlWorkloadPlugin(environment, instance_id, label=label, base=base)


@Factory(
    plugin_id=METTA_PLUGIN_ID_KUBERNETES_HELM_WORKLOAD,
    interfaces=[METTA_PLUGIN_INTERFACE_ROLE_WORKLOAD, METTA_PLUGIN_INTERFACE_ROLE_HEALTHCHECK],
)
def metta_plugin_factory_workload_kubernetes_helm(
    environment: Environment,
    instance_id: str = "",
    label: str = KUBERNETES_HELM_WORKLOAD_CONFIG_LABEL,
    base: Any = KUBERNETES_HELM_WORKLOAD_CONFIG_BASE,
):
    """Create a metta kubernetes spec workload plugin."""
    return KubernetesHelmWorkloadPlugin(environment, instance_id, label=label, base=base)


@Factory(
    plugin_id=METTA_PLUGIN_ID_KUBERNETES_CLI,
    interfaces=[METTA_PLUGIN_INTERFACE_ROLE_CLI],
)
def metta_terraform_factory_cli_kubernetes(environment: Environment, instance_id: str = ""):
    """Create a kubernetes cli plugin."""
    return KubernetesCliPlugin(environment, instance_id)


# ----- SetupTools EntryPoint METTA BootStrapping -----


# pylint: disable=unused-argument
def bootstrap_environment(environment: Environment):
    """METTA_Terraform bootstrap.

    Currently we only use this to import plugins.

    Parameters:
    -----------
    env (Environment) : an environment which should have validation config added to.

    """
