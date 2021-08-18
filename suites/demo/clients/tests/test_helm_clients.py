"""

Test that some clients work.

Here test the kube helm workload.

"""
import logging

import pytest

from mirantis.testing.metta_kubernetes.helm_workload import Status

logger = logging.getLogger("test_clients.helm")

DEFAULT_K8S_NAMESPACE = "default"


@pytest.fixture(scope="module")
def metrics_workload(environment_up):
    """Get the helm metrics workload from fixtures/yml."""
    # we have a docker run workload fixture called "metrics-helm-workload"
    plugin = environment_up.fixtures().get_plugin(instance_id="metrics-helm-workload")

    logger.info("Starting helm instance")
    plugin.prepare(environment_up.fixtures())
    plugin.apply(wait=True)

    yield plugin

    plugin.destroy()


def test_kubernetes_helm_workload(metrics_workload, kubeapi_client):
    """Test that we can get a helm workload to run."""
    apps_v1 = kubeapi_client.get_api("AppsV1Api")
    """ kubernetes client api we will use to detect the helm release in k8s """

    # use some instance overrides
    metrics_workload.namespace = DEFAULT_K8S_NAMESPACE

    info = metrics_workload.info(deep=False)

    instance_list = metrics_workload.list()
    logger.info("Helm releases : %s", instance_list)

    nsd = apps_v1.list_namespaced_deployment(namespace=DEFAULT_K8S_NAMESPACE)
    logger.info(
        "Namespace (%s) deployments: %s",
        DEFAULT_K8S_NAMESPACE,
        {item.metadata.name: item.status for item in nsd.items},
    )

    helm_release_name = info["release"]["name"]
    deployment_name = f"{helm_release_name}-metrics-server"

    deployment = apps_v1.read_namespaced_deployment(
        deployment_name,
        metrics_workload.namespace,
    )
    logger.info("Looks like the helm deployment: %s", deployment.metadata.annotations)

    logger.info("Running helm instance tests")
    metrics_workload.test()

    logger.info("Checking helm instance status")
    status = metrics_workload.status()
    assert status.name == helm_release_name
    assert status.status == Status.DEPLOYED
    logger.info("--> Status: %s", status.description)
