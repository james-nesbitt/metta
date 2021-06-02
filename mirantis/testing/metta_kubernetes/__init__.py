"""

METTA Kubernetes.

metta contrib functionality for Kubernetes.  In particular to provide plugins
for kubernetes clients and kubernetes workloads.

"""

from typing import Any

from mirantis.testing.metta.plugin import Factory
from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.client import METTA_PLUGIN_TYPE_CLIENT
from mirantis.testing.metta.workload import METTA_PLUGIN_TYPE_WORKLOAD
from mirantis.testing.metta_cli.base import METTA_PLUGIN_TYPE_CLI

from .kubeapi_client import KubernetesApiClientPlugin, METTA_PLUGIN_ID_KUBERNETES_CLIENT
from .deployment_workload import (KubernetesDeploymentWorkloadPlugin,
                                  METTA_PLUGIN_ID_KUBERNETES_DEPLOYMENT_WORKLOAD,
                                  KUBERNETES_DEPLOYMENT_WORKLOAD_CONFIG_LABEL,
                                  KUBERNETES_DEPLOYMENT_WORKLOAD_CONFIG_BASE)
from .yaml_workload import (KubernetesYamlWorkloadPlugin, METTA_PLUGIN_ID_KUBERNETES_YAML_WORKLOAD,
                            KUBERNETES_YAML_WORKLOAD_CONFIG_LABEL,
                            KUBERNETES_YAML_WORKLOAD_CONFIG_BASE)
from .helm_workload import (KubernetesHelmWorkloadPlugin, METTA_PLUGIN_ID_KUBERNETES_HELM_WORKLOAD,
                            KUBERNETES_HELM_WORKLOAD_CONFIG_LABEL,
                            KUBERNETES_HELM_WORKLOAD_CONFIG_BASE)
from .cli import KubernetesCliPlugin


@Factory(plugin_type=METTA_PLUGIN_TYPE_CLIENT, plugin_id=METTA_PLUGIN_ID_KUBERNETES_CLIENT)
def metta_plugin_factory_client_kubernetes(
        environment: Environment, instance_id: str = '', kube_config_file: str = ''):
    """Create an metta kubernetes client plugin."""
    return KubernetesApiClientPlugin(
        environment, instance_id, kube_config_file)


@Factory(plugin_type=METTA_PLUGIN_TYPE_WORKLOAD,
         plugin_id=METTA_PLUGIN_ID_KUBERNETES_DEPLOYMENT_WORKLOAD)
def metta_plugin_factory_workload_kubernetes_deployment(
        environment: Environment, instance_id: str = '',
        label: str = KUBERNETES_DEPLOYMENT_WORKLOAD_CONFIG_LABEL,
        base: Any = KUBERNETES_DEPLOYMENT_WORKLOAD_CONFIG_BASE):
    """Create an metta kubernetes spec workload plugin."""
    return KubernetesDeploymentWorkloadPlugin(
        environment, instance_id, label=label, base=base)


@Factory(plugin_type=METTA_PLUGIN_TYPE_WORKLOAD, plugin_id=METTA_PLUGIN_ID_KUBERNETES_YAML_WORKLOAD)
def metta_plugin_factory_workload_kubernetes_yaml(
        environment: Environment, instance_id: str = '',
        label: str = KUBERNETES_YAML_WORKLOAD_CONFIG_LABEL,
        base: Any = KUBERNETES_YAML_WORKLOAD_CONFIG_BASE):
    """Create an metta kubernetes spec workload plugin."""
    return KubernetesYamlWorkloadPlugin(
        environment, instance_id, label=label, base=base)


@Factory(plugin_type=METTA_PLUGIN_TYPE_WORKLOAD, plugin_id=METTA_PLUGIN_ID_KUBERNETES_HELM_WORKLOAD)
def metta_plugin_factory_workload_kubernetes_helm(
        environment: Environment, instance_id: str = '',
        label: str = KUBERNETES_HELM_WORKLOAD_CONFIG_LABEL,
        base: Any = KUBERNETES_HELM_WORKLOAD_CONFIG_BASE):
    """Create an metta kubernetes spec workload plugin."""
    return KubernetesHelmWorkloadPlugin(
        environment, instance_id, label=label, base=base)


@Factory(plugin_type=METTA_PLUGIN_TYPE_CLI, plugin_id=METTA_PLUGIN_ID_KUBERNETES_CLIENT)
def metta_terraform_factory_cli_kubernetes(
        environment: Environment, instance_id: str = ''):
    """Create a kubernetes cli plugin."""
    return KubernetesCliPlugin(environment, instance_id)


# ----- SetupTools EntryPoint METTA BootStrapping -----


# pylint: disable=unused-argument
def bootstrap(environment: Environment):
    """METTA_Terraform bootstrap.

    Currently we only use this to import plugins.

    Parameters:
    -----------
    env (Environment) : an environment which should have validation config added to.

    """
