"""

Healthcheck plugin that uses kubeapi to check on k8s health.

"""

import logging

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.healthcheck import Health, HealthStatus

from .kubeapi_client import KubernetesApiClientPlugin, node_status_condition

logger = logging.getLogger('metta_kubernetes.kubeapi_health')


class KubeApiHealthCheckPlugin:
    """Metta healthcheck plugin that checks on kubernetes health using an api client."""

    def __init__(self, environment: Environment, instance_id: str,
                 kubeapi_client: KubernetesApiClientPlugin):
        """Create a healthcheck plugin for a specific API plugin instance."""
        self.environment = environment
        self.instance_id = instance_id

        self.kubeapi_client = kubeapi_client
        """K8s API plugin which will be used for health checks."""

    def health(self) -> Health:
        """Determine the health of the K8s instance."""
        k8s_health = Health(status=HealthStatus.UNKNOWN)

        for test_health_function in [
            self.test_k8s_readyz,
            self.test_k8s_node_health,
            self.test_k8s_allpod_health
        ]:
            test_health = test_health_function()
            k8s_health.merge(test_health)

        return k8s_health

    def test_k8s_readyz(self):
        """Check if kubernetes thinks the pod is healthy."""
        health = Health()

        core_v1_api = self.kubeapi_client.get_api('CoreV1Api')

        unhealthy_pod_count = 0
        for pod in core_v1_api.list_pod_for_all_namespaces().items:
            if pod.status.phase == "Failed":
                logger.error("Kubernetes reports a pod failed: %s", pod.metadata.name)
                unhealthy_pod_count += 1
        if unhealthy_pod_count == 0:
            health.info("Kubernetes readyz reports ready")
        elif unhealthy_pod_count < 2:
            health.warning("Kubernetes Reports some pods are failed")
        else:
            health.error("Kubernetes Reports cluster is unhealthy (pod health)")

        return health

    def test_k8s_node_health(self):
        """Check if kubernetes thinks the nodes are healthy."""
        health = Health()

        no_issues = True
        for node in self.kubeapi_client.nodes():
            kubelet_condition = node_status_condition(node, 'KubeletReady')
            if not kubelet_condition.status == 'True':
                health.error(f"Node kubelet is not ready: {node.metadata.name}")
                no_issues = False

        if no_issues:
            health.info("Kubernetes reports all nodes are health.")

        return health

    def test_k8s_allpod_health(self):
        """Check if kubernetes thinks all the pods are healthy."""
        health = Health()

        core_v1_api = self.kubeapi_client.get_api('CoreV1Api')

        unhealthy_pod_count = 0
        for pod in core_v1_api.list_pod_for_all_namespaces().items:
            if pod.status.phase == "Failed":
                logger.error("Kubernetes reports a pod failed: %s", pod.metadata.name)
                unhealthy_pod_count += 1
        if unhealthy_pod_count == 0:
            health.info("Kubernetes reports all pods as healthy")
        elif unhealthy_pod_count < 2:
            health.warning("Kubernetes Reports some pods are failed")
        else:
            health.error("Kubernetes Reports cluster is unhealthy (pod health)")

        return health
