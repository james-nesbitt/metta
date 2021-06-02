"""

Kubernetes workload plugin.

This plugin uses the kube_api client to deploy workloads to kubernetes, from a deployment
definition from configuration.

"""

import logging
from typing import Any

import kubernetes

from mirantis.testing.metta.fixtures import Fixtures
from mirantis.testing.metta.client import METTA_PLUGIN_TYPE_CLIENT
from mirantis.testing.metta.workload import WorkloadBase, WorkloadInstanceBase

from .kubeapi_client import METTA_PLUGIN_ID_KUBERNETES_CLIENT

logger = logging.getLogger('metta.contrib.kubernetes.workload.deployment')

KUBERNETES_DEPLOYMENT_WORKLOAD_CONFIG_LABEL = 'kubernetes'
KUBERNETES_DEPLOYMENT_WORKLOAD_CONFIG_BASE = 'workload.deployment'

KUBERNETES_DEPLOYMENT_WORKLOAD_CONFIG_KEY_NAMESPACE = "namespace"
KUBERNETES_DEPLOYMENT_WORKLOAD_CONFIG_KEY_BODY = "body"

METTA_PLUGIN_ID_KUBERNETES_DEPLOYMENT_WORKLOAD = 'metta_kubernetes_deployment'
""" workload plugin_id for the metta_kubernetes deployment plugin """


class KubernetesDeploymentWorkloadPlugin(WorkloadBase):
    """Metta workload plugin for Kubernetes workload."""

    def __init__(self, environment, instance_id,
                 label: str = KUBERNETES_DEPLOYMENT_WORKLOAD_CONFIG_LABEL,
                 base: Any = KUBERNETES_DEPLOYMENT_WORKLOAD_CONFIG_BASE):
        """Run the super constructor but also set class properties.

        This implements the args part of the client interface.

        Here we expect to receive a path to a KUBECONFIG file with a context set
        and we create a Kubernetes client for use.  After that this can provide
        Core api clients as per the kubernetes SDK

        Parameters:
        -----------
        config_file (str): String path to the kubernetes config file to use

        """
        self.environment = environment
        """ Environemnt in which this plugin exists """
        self.instance_id = instance_id
        """ Unique id for this plugin instance """

        self.config_label = label
        """ configerus load label that should contain all of the config """
        self.config_base = base
        """ configerus get key that should contain all tf config """

    def create_instance(self, fixtures: Fixtures):
        """Create a workload instance from a set of fixtures.

        Parameters:
        ----------
        fixtures (Fixtures) : a set of fixtures that this workload will use to
            retrieve a kubernetes client plugin.

        """
        try:
            client = fixtures.get_plugin(plugin_type=METTA_PLUGIN_TYPE_CLIENT,
                                         plugin_id=METTA_PLUGIN_ID_KUBERNETES_CLIENT)
        except KeyError as err:
            raise NotImplementedError("Workload could not find the needed client: "
                                      f"{METTA_PLUGIN_ID_KUBERNETES_CLIENT}") from err

        workload_config = self.environment.config.load(self.config_label)

        name = workload_config.get([self.config_base,
                                    KUBERNETES_DEPLOYMENT_WORKLOAD_CONFIG_KEY_BODY,
                                    'metadata.name'],
                                   default='not-declared')
        namespace = workload_config.get(
            [self.config_base, KUBERNETES_DEPLOYMENT_WORKLOAD_CONFIG_KEY_NAMESPACE])
        body = workload_config.get(
            [self.config_base, KUBERNETES_DEPLOYMENT_WORKLOAD_CONFIG_KEY_BODY])

        return KubernetesDeploymentWorkloadInstance(
            client, namespace, name, body)

    def info(self):
        """Return dict data about this plugin for introspection."""
        workload_config = self.environment.config.load(self.config_label)

        return {
            'workload': {
                'deployment': {
                    'namespace': workload_config.get(
                        [self.config_base, KUBERNETES_DEPLOYMENT_WORKLOAD_CONFIG_KEY_NAMESPACE]),
                    'body': workload_config.get(
                        [self.config_base, KUBERNETES_DEPLOYMENT_WORKLOAD_CONFIG_KEY_BODY])
                },
                'required_fixtures': {
                    'kubernetes': {
                        'plugin_type': METTA_PLUGIN_TYPE_CLIENT,
                        'plugin_id': 'metta_kubernetes'
                    }
                }
            }
        }


class KubernetesDeploymentWorkloadInstance(WorkloadInstanceBase):
    """Workload plugin instance, for managing individual deployment runs."""

    def __init__(self, client, namespace, name, body):
        """Set initial workload instance state."""
        self.client = client
        self.namespace = namespace
        self.name = name
        self.body = body

        self.deployment = None

        self.read()

    def read(self):
        """Retrieve the deployment job."""
        if self.deployment is None:
            apps_v1 = self.client.get_api('AppsV1Api')

            try:
                self.deployment = apps_v1.read_namespaced_deployment(
                    self.name, self.namespace)
            except kubernetes.client.rest.ApiException:
                self.deployment = None

        return self.deployment

    def apply(self):
        """Run the workload."""
        apps_v1 = self.client.get_api('AppsV1Api')
        self.deployment = apps_v1.create_namespaced_deployment(
            body=self.body, namespace=self.namespace)

        return self.deployment

    def destroy(self):
        """Destroy any created resources."""
        body = kubernetes.client.V1DeleteOptions(
            propagation_policy='Foreground',
            grace_period_seconds=5)

        apps_v1 = self.client.get_api('AppsV1Api')
        status = apps_v1.delete_namespaced_deployment(
            name=self.name, namespace=self.namespace, body=body)

        self.deployment = None

        return status
