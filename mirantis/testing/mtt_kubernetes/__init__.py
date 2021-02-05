"""

MTT Kubernetes

MTT contrib functionality for Kubernetes.  In particular to provide plugins for
kubernetes clients and kubernetes workloads.

"""

import os
from configerus.config import Config

from mirantis.testing.mtt import plugin as mtt_plugin

from .plugins.client import KubernetesClientPlugin
from .plugins.workload import KubernetesSpecFilesWorkloadPlugin

MTT_PLUGIN_ID_KUBERNETES_CLIENT='mtt_kubernetes'
""" client plugin_id for the mtt dummy plugin """
@mtt_plugin.Factory(type=mtt_plugin.Type.CLIENT, plugin_id=MTT_PLUGIN_ID_KUBERNETES_CLIENT)
def mtt_plugin_factory_client_kubernetes(config:Config, instance_id:str = ''):
    """ create an mtt kubernetes client plugin """
    return KubernetesClientPlugin(config, instance_id)


MTT_PLUGIN_ID_KUBERNETES_SPEC_WORKLAOD='mtt_kubernetes_spec'
""" workload plugin_id for the mtt_kubernetes spec plugin """
@mtt_plugin.Factory(type=mtt_plugin.Type.WORKLOAD, plugin_id=MTT_PLUGIN_ID_KUBERNETES_SPEC_WORKLAOD)
def mtt_plugin_factory_workload_kubernetes_spec(config:Config, instance_id:str = ''):
    """ create an mtt kubernetes spec workload plugin """
    return KubernetesSpecFilesWorkloadPlugin(config, instance_id)


def configerus_bootstrap(config:Config):
    """ MTT_Kubernetes configerus bootstrap

    We dont't take any action.  Our purpose is to run the above factory
    decorators to register our plugins.

    """
    pass
