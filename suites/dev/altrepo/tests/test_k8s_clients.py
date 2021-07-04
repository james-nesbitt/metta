"""

Test that some clients work

"""

import logging

from mirantis.testing.metta.client import METTA_PLUGIN_INTERFACE_ROLE_CLIENT
from mirantis.testing.metta.workload import METTA_PLUGIN_INTERFACE_ROLE_WORKLOAD
from mirantis.testing.metta_kubernetes import METTA_PLUGIN_ID_KUBERNETES_CLIENT

logger = logging.getLogger("test_clients")

DEFAULT_K8S_NAMESPACE = "default"

# this is a test suite, and lazy interpolation is not very strong
# pylint: disable=logging-format-interpolation


def test_launchpad_kubectl_client(environment_up):
    """did we get a good kubectl client"""

    logger.info("Getting K8s client")
    kubectl_client = environment_up.fixtures.get_plugin(
        plugin_type=METTA_PLUGIN_INTERFACE_ROLE_CLIENT,
        plugin_id=METTA_PLUGIN_ID_KUBERNETES_CLIENT,
    )

    core_v1 = kubectl_client.get_api("core_v1Api")
    nas = core_v1.read_namespace(name=DEFAULT_K8S_NAMESPACE)
    logger.info("--> Dumping namespace: %s", nas)

    assert nas.metadata.name == DEFAULT_K8S_NAMESPACE, "Wrong namespace given"


def test_kubernetes_deployment_workload(environment_up):
    """test that we can get a k8s deployment workload to run"""

    sanity_kubernetes_deployment = environment_up.fixtures.get_plugin(
        plugin_type=METTA_PLUGIN_INTERFACE_ROLE_WORKLOAD,
        instance_id="sanity_kubernetes_deployment",
    )
    """ workload plugin """

    instance = sanity_kubernetes_deployment.create_instance(environment_up.fixtures)

    deployment = instance.apply()
    assert deployment is not None
    logger.info("Deployment name: %s", deployment.metadata.name)

    status = instance.destroy()
    assert status is not None
    assert status.code is None
    logger.info("Deployment status after destroy: %s", status)
