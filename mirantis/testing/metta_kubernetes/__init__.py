"""

metta Kubernetes

metta contrib functionality for Kubernetes.  In particular to provide plugins for
kubernetes clients and kubernetes workloads.

"""

import os
from typing import List, Any

from mirantis.testing.metta.plugin import Factory, Type
from mirantis.testing.metta.environment import Environment

from .kubeapi_client import KubernetesApiClientPlugin
from .deployment_workload import KubernetesDeploymentWorkloadPlugin, KUBERNETES_DEPLOYMENT_WORKLOAD_CONFIG_LABEL, KUBERNETES_DEPLOYMENT_WORKLOAD_CONFIG_BASE
from .helm_workload import KubernetesHelmWorkloadPlugin, KUBERNETES_HELM_WORKLOAD_CONFIG_LABEL, KUBERNETES_HELM_WORKLOAD_CONFIG_BASE

METTA_PLUGIN_ID_KUBERNETES_CLIENT = 'metta_kubernetes'
""" client plugin_id for the metta dummy plugin """


@Factory(type=Type.CLIENT, plugin_id=METTA_PLUGIN_ID_KUBERNETES_CLIENT)
def metta_plugin_factory_client_kubernetes(
        environment: Environment, instance_id: str = '', kube_config_file: str = ''):
    """ create an metta kubernetes client plugin """
    return KubernetesApiClientPlugin(
        environment, instance_id, kube_config_file)


METTA_PLUGIN_ID_KUBERNETES_DEPLOYMENT_WORKLAOD = 'metta_kubernetes_deployment'
""" workload plugin_id for the metta_kubernetes deployment plugin """


@Factory(type=Type.WORKLOAD,
         plugin_id=METTA_PLUGIN_ID_KUBERNETES_DEPLOYMENT_WORKLAOD)
def metta_plugin_factory_workload_kubernetes_deployment(
        environment: Environment, instance_id: str = '', label: str = KUBERNETES_DEPLOYMENT_WORKLOAD_CONFIG_LABEL, base: Any = KUBERNETES_DEPLOYMENT_WORKLOAD_CONFIG_BASE):
    """ create an metta kubernetes spec workload plugin """
    return KubernetesDeploymentWorkloadPlugin(
        environment, instance_id, label=label, base=base)


METTA_PLUGIN_ID_KUBERNETES_HELM_WORKLAOD = 'metta_kubernetes_helm'
""" workload plugin_id for the metta_kubernetes helm plugin """


@Factory(type=Type.WORKLOAD,
         plugin_id=METTA_PLUGIN_ID_KUBERNETES_HELM_WORKLAOD)
def metta_plugin_factory_workload_kubernetes_helm(
        environment: Environment, instance_id: str = '', label: str = KUBERNETES_HELM_WORKLOAD_CONFIG_LABEL, base: Any = KUBERNETES_HELM_WORKLOAD_CONFIG_BASE):
    """ create an metta kubernetes spec workload plugin """
    return KubernetesHelmWorkloadPlugin(
        environment, instance_id, label=label, base=base)


""" SetupTools EntryPoint METTA BootStrapping """


def bootstrap(environment: Environment):
    """ METTA_Kubernetes bootstrap

    We dont't take any action.  Our purpose is to run the above factory
    decorators to register our plugins.

    """
    pass
