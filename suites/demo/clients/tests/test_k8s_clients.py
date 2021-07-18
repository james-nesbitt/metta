"""

Test that some clients work.

Here test the kubeapi clientand the kube deplyment workloads.

"""
import logging

import pytest


logger = logging.getLogger("test_clients.kubeapi")

DEFAULT_K8S_NAMESPACE = "default"


@pytest.fixture(scope="module")
def sanity_kubernetes_deployment(environment_up):
    """Get the sanity kube deployment workload from fixtures/yml."""
    # we have a kube deploment workload fixture called "sanity-kubernetes-deployment"
    plugin = environment_up.fixtures.get_plugin(instance_id="sanity-kubernetes-deployment")
    plugin.prepare(environment_up.fixtures)
    plugin.apply()

    yield plugin

    plugin.destroy()


def test_launchpad_kubeapi_client(kubeapi_client):
    """did we get a good kubectl client"""
    core_v1 = kubeapi_client.get_api("CoreV1Api")
    namespace = core_v1.read_namespace(name=DEFAULT_K8S_NAMESPACE)
    print(f"--> Dumping namespace: {namespace}")

    assert namespace.metadata.name == DEFAULT_K8S_NAMESPACE, "Wrong namespace given"


def test_kubernetes_deployment_workload(sanity_kubernetes_deployment):
    """test that we can get a k8s deployment workload to run"""

    assert sanity_kubernetes_deployment is not None
    deployment = sanity_kubernetes_deployment.read()
    logger.info("Deployment name: %s", deployment.metadata.name)
