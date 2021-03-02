"""

Kubernetes workload plugins

"""

import logging
from typing import List, Any

import kubernetes

from mirantis.testing.metta.plugin import Type
from mirantis.testing.metta.fixtures import Fixtures
from mirantis.testing.metta.workload import WorkloadBase, WorkloadInstanceBase

logger = logging.getLogger('metta.contrib.kubernetes.workload.deployment')

KUBERNETES_DEPLOYMENT_WORKLOAD_CONFIG_LABEL = 'kubernetes'
KUBERNETES_DEPLOYMENT_WORKLOAD_CONFIG_BASE = 'workload.deployment'

KUBERNETES_DEPLOYMENT_WORKLOAD_CONFIG_KEY_NAMESPACE = "namespace"
KUBERNETES_DEPLOYMENT_WORKLOAD_CONFIG_KEY_BODY = "body"


class KubernetesDeploymentWorkloadPlugin(WorkloadBase):
    """ Kubernetes workload class """

    def __init__(self, environment, instance_id,
                 label: str = KUBERNETES_DEPLOYMENT_WORKLOAD_CONFIG_LABEL, base: Any = KUBERNETES_DEPLOYMENT_WORKLOAD_CONFIG_BASE):
        """ Run the super constructor but also set class properties

        This implements the args part of the client interface.

        Here we expect to receive a path to a KUBECONFIG file with a context set
        and we create a Kubernetes client for use.  After that this can provide
        Core api clients as per the kubernetes SDK

        Parameters:
        -----------

        config_file (str): String path to the kubernetes config file to use

        """
        WorkloadBase.__init__(self, environment, instance_id)

        self.config_label = label
        """ configerus load label that should contain all of the config """
        self.config_base = base
        """ configerus get key that should contain all tf config """

    def create_instance(self, fixtures: Fixtures):
        """ Create a workload instance from a set of fixtures

        Parameters:
        -----------

        fixtures (Fixtures) : a set of fixtures that this workload will use to
            retrieve a kubernetes client plugin.

        """

        try:
            client = fixtures.get_plugin(
                type=Type.CLIENT, plugin_id='metta_kubernetes')
        except KeyError as e:
            raise NotImplementedError(
                "Workload could not find the needed client: {}".format('metta_kubernetes'))

        workload_config = self.environment.config.load(self.config_label)

        name = name = workload_config.get(
            [self.config_base, KUBERNETES_DEPLOYMENT_WORKLOAD_CONFIG_KEY_BODY, 'metadata.name'])
        namespace = workload_config.get(
            [self.config_base, KUBERNETES_DEPLOYMENT_WORKLOAD_CONFIG_KEY_NAMESPACE], exception_if_missing=True)
        body = workload_config.get(
            [self.config_base, KUBERNETES_DEPLOYMENT_WORKLOAD_CONFIG_KEY_BODY], exception_if_missing=True)

        return KubernetesDeploymentWorkloadInstance(
            client, namespace, name, body)

    def info(self):
        """ Return dict data about this plugin for introspection """
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
                        'type': Type.CLIENT.value,
                        'plugin_id': 'metta_kubernetes'
                    }
                }
            }
        }


class KubernetesDeploymentWorkloadInstance(WorkloadInstanceBase):

    def __init__(self, client, namespace, name, body):
        self.client = client
        self.namespace = namespace
        self.name = name
        self.body = body

        self.deployment = None

        self.read()

    def read(self):
        """ retrieve the deployment job """
        if self.deployment is None:
            k8s_apps_v1 = kubernetes.client.AppsV1Api(
                self.client.api_client)

            try:
                self.deployment = k8s_apps_v1.read_namespaced_deployment(
                    self.name, self.namespace)
            except Exception:
                self.deployment = None

        return self.deployment

    def apply(self):
        """ Run the workload

        @NOTE Needs a kubernetes client fixture to run.  Use .set_fixtures() first

        """

        k8s_apps_v1 = kubernetes.client.AppsV1Api(
            self.client.api_client)
        self.deployment = k8s_apps_v1.create_namespaced_deployment(
            body=self.body, namespace=self.namespace)

        return self.deployment

    def destroy(self):
        """ destroy any created resources """

        body = kubernetes.client.V1DeleteOptions(
            propagation_policy='Foreground',
            grace_period_seconds=5)

        k8s_apps_v1 = kubernetes.client.AppsV1Api(
            self.client.api_client)
        self.status = k8s_apps_v1.delete_namespaced_deployment(
            name=self.name, namespace=self.namespace, body=body)

        self.deployment = None

        return self.status
