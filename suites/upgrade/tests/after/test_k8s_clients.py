"""

Test that some clients work

"""

import logging

from mirantis.testing.metta.plugin import Type
from mirantis.testing.metta_kubernetes import METTA_PLUGIN_ID_KUBERNETES_CLIENT

logger = logging.getLogger("test_clients")


@pytest.mark.second
def test_launchpad_kubectl_client(environment_up):
    """ did we get a good kubectl client """

    logger.info("Getting K8s client")
    kubectl_client = environment_up.fixtures.get_plugin(type=Type.CLIENT,
                                                        plugin_id=METTA_PLUGIN_ID_KUBERNETES_CLIENT)

    coreV1 = kubectl_client.get_CoreV1Api_client()
    ns = coreV1.read_namespace(name="kube-system")
    print("NS: {}".format(ns))

    assert ns.metadata.name == "kube-system", "Wrong namespace given"


@pytest.mark.second
def test_kubernetes_deployment_workload(environment_up):
    """ test that we can get a k8s workload to run """

    sanity_kubernetes_deployment = environment_up.fixtures.get_plugin(type=Type.WORKLOAD,
                                                                      instance_id='sanity_kubernetes_deployment')
    """ workload plugin """

    instance = sanity_kubernetes_deployment.create_instance(
        environment_up.fixtures)

    deployment = instance.apply()
    assert deployment is not None
    print(deployment.metadata.name)

    status = instance.destroy()
    assert status is not None
    assert status.code is None
    print(status)
