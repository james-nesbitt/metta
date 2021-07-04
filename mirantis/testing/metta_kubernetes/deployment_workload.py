"""

Kubernetes workload plugin.

This plugin uses the kube_api client to deploy workloads to kubernetes, from a deployment
definition from configuration.

"""

import logging
from typing import Any, Dict

import kubernetes

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.fixtures import Fixtures
from mirantis.testing.metta.healthcheck import Health, HealthStatus

from .kubeapi_client import KubernetesApiClientPlugin, METTA_PLUGIN_ID_KUBERNETES_CLIENT

logger = logging.getLogger("metta.contrib.kubernetes.workload.deployment")

METTA_PLUGIN_ID_KUBERNETES_DEPLOYMENT_WORKLOAD = "metta_kubernetes_deployment_workload"
""" workload plugin_id for the metta_kubernetes deployment plugin """

KUBERNETES_DEPLOYMENT_WORKLOAD_CONFIG_LABEL = "kubernetes"
KUBERNETES_DEPLOYMENT_WORKLOAD_CONFIG_BASE = "workload.deployment"

KUBERNETES_DEPLOYMENT_WORKLOAD_CONFIG_KEY_NAMESPACE = "namespace"
KUBERNETES_DEPLOYMENT_WORKLOAD_CONFIG_KEY_BODY = "body"


# pylint: disable=too-many-instance-attributes
class KubernetesDeploymentWorkloadPlugin:
    """Metta workload plugin for Kubernetes workload."""

    def __init__(
        self,
        environment: Environment,
        instance_id: str,
        label: str = KUBERNETES_DEPLOYMENT_WORKLOAD_CONFIG_LABEL,
        base: Any = KUBERNETES_DEPLOYMENT_WORKLOAD_CONFIG_BASE,
    ):
        """Run the super constructor but also set class properties.

        This implements the args part of the client interface.

        Here we expect to receive a path to a KUBECONFIG file with a context set
        and we create a Kubernetes client for use.  After that this can provide
        Core api clients as per the kubernetes SDK

        Parameters:
        -----------
        config_file (str): String path to the kubernetes config file to use

        """
        self._environment: Environment = environment
        """ Environemnt in which this plugin exists """
        self._instance_id: str = instance_id
        """ Unique id for this plugin instance """

        self._config_label: str = label
        """ configerus load label that should contain all of the config """
        self._config_base: str = base
        """ configerus get key that should contain all tf config """

        workload_config = self._environment.config.load(self._config_label)

        self.name: str = workload_config.get(
            [
                self._config_base,
                KUBERNETES_DEPLOYMENT_WORKLOAD_CONFIG_KEY_BODY,
                "metadata.name",
            ],
            default="not-declared",
        )
        """Kubernetes deployment name string."""
        self.namespace: str = workload_config.get(
            [self._config_base, KUBERNETES_DEPLOYMENT_WORKLOAD_CONFIG_KEY_NAMESPACE]
        )
        """Kubernetes namespace to use for the deployment."""
        self.body: Dict[str, Any] = workload_config.get(
            [self._config_base, KUBERNETES_DEPLOYMENT_WORKLOAD_CONFIG_KEY_BODY]
        )
        """Kubernetes deployment definition dict."""

        self._kubeapi_client: KubernetesApiClientPlugin = None
        """KubeAPI client for connecting to kubernetes."""

        self.deployment: object = None
        """KubeAPI get deployment result."""

    # deep argument is an info() standard across plugins
    # pylint: disable=unused-argument
    def info(self, deep: bool = False):
        """Return dict data about this plugin for introspection."""
        workload_config = self._environment.config.load(self._config_label)

        if self._kubeapi_client is None:
            # let's take a stab at finding a client for declarative cases
            try:
                kubeclient = self._environment.fixtures.get_plugin(
                    plugin_id=METTA_PLUGIN_ID_KUBERNETES_CLIENT,
                )
                kubeclient_info = kubeclient.info()
            except KeyError:
                # we will just work around a missing kube api plugin
                kubeclient_info = None
        else:
            kubeclient_info = self._kubeapi_client.info()

        return {
            "workload": {
                "deployment": {
                    "namespace": workload_config.get(
                        [
                            self._config_base,
                            KUBERNETES_DEPLOYMENT_WORKLOAD_CONFIG_KEY_NAMESPACE,
                        ]
                    ),
                    "body": workload_config.get(
                        [
                            self._config_base,
                            KUBERNETES_DEPLOYMENT_WORKLOAD_CONFIG_KEY_BODY,
                        ]
                    ),
                },
                "required_fixtures": {
                    "kubernetes": {
                        "plugin_id": METTA_PLUGIN_ID_KUBERNETES_CLIENT,
                        "kube_client": kubeclient_info,
                    }
                },
            }
        }

    def prepare(self, fixtures: Fixtures = None):
        """Find the kubeapi client from a set of fixtures and retrieve config
        for running the workload.

        Parameters:
        ----------
        fixtures (Fixtures) : a set of fixtures that this workload will use to
            retrieve a kubernetes client plugin.

        """
        if fixtures is None:
            fixtures = self._environment.fixtures

        try:
            self._kubeapi_client: KubernetesApiClientPlugin = fixtures.get_plugin(
                plugin_id=METTA_PLUGIN_ID_KUBERNETES_CLIENT
            )
        except KeyError as err:
            raise NotImplementedError(
                "Workload could not find the needed client: "
                f"{METTA_PLUGIN_ID_KUBERNETES_CLIENT}"
            ) from err

    def apply(self):
        """Run the workload."""
        apps_v1 = self._kubeapi_client.get_api("AppsV1Api")
        return apps_v1.create_namespaced_deployment(
            body=self.body, namespace=self.namespace
        )

    def destroy(self):
        """Destroy any created resources."""
        body = kubernetes.client.V1DeleteOptions(
            propagation_policy="Foreground", grace_period_seconds=5
        )

        apps_v1 = self._kubeapi_client.get_api("AppsV1Api")
        status = apps_v1.delete_namespaced_deployment(
            name=self.name, namespace=self.namespace, body=body
        )

        return status

    def read(self):
        """Retrieve the deployment job."""
        apps_v1 = self._kubeapi_client.get_api("AppsV1Api")

        try:
            return apps_v1.read_namespaced_deployment(self.name, self.namespace)
        except kubernetes.client.rest.ApiException:
            return None

    # INTERFACE: healthcheck
    def health(self) -> Health:
        """Determine the health of the K8s deployment."""
        dep_health = Health(source=self._instance_id, status=HealthStatus.UNKNOWN)

        for test_health_function in [self._health_deployment_status]:
            test_health = test_health_function()
            dep_health.merge(test_health)

        return dep_health

    def _health_deployment_status(self):
        """Check if kubernetes thinks the deployment is healthy."""
        health = Health(source=self._instance_id)

        apps_v1 = self._kubeapi_client.get_api("AppsV1Api")

        try:
            deployment = apps_v1.read_namespaced_deployment(self.name, self.namespace)

            status = deployment.status

            if status is None:
                health.error(
                    f"Deployment: [{self.namespace}/{self.name}] retrieved no status"
                )
            else:
                for condition in status.conditions:
                    if condition.status == "True":
                        health.info(
                            f"Deployment: [{self.namespace}/{self.name}] {condition.type} -> {condition.message}"
                        )
                    else:
                        health.error(
                            f"Deployment: [{self.namespace}/{self.name}] {condition.type} -> {condition.message}"
                        )

        except kubernetes.client.rest.ApiException as err:
            health.error(f"K8S REST API exception occured: {err}")

        return health
