"""

Test that some clients work

"""

import logging

from uctt.contrib.kubernetes import UCTT_PLUGIN_ID_KUBERNETES_CLIENT

logger = logging.getLogger("test_clients")


def test_launchpad_kubectl_client(environment_up, launchpad):
    """ did we get a good kubectl client """

    logger.info("Getting K8s client")
    kubectl_client = launchpad.get_client(
        plugin_id=UCTT_PLUGIN_ID_KUBERNETES_CLIENT)

    coreV1 = kubectl_client.get_CoreV1Api_client()
    ns = coreV1.read_namespace(name="kube-system")
    print("NS: {}".format(ns))

    assert ns.metadata.name == "kube-system", "Wrong namespace given"


def test_kubernetes_deployment_workload(environment_up):
    """ test that we can get a k8s workload to run """

    sanity_kubernetes_deployment = environment_up.fixtures.get_plugin(
        instance_id='sanity_kubernetes_deployment')
    """ workload plugin """

    sanity_kubernetes_deployment.set_fixtures(environment_up.fixtures)

    deployment = sanity_kubernetes_deployment.apply()
    assert deployment is not None
    print(deployment.metadata.name)

    status = sanity_kubernetes_deployment.destroy()
    assert status is not None
    assert status.code is None
    print(status)
