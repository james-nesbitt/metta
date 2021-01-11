"""

Test that some clients work

"""

import logging

logger = logging.getLogger("test_clients")

def test_launchpad_kubectl_client(provisioner):
    """ did we get a good kubectl client


    """
    logger.info("Getting K8s client")
    kubectl_client = provisioner.get_client("kubernetes")

    coreV1 = kubectl_client.get_CoreV1Api_client()
    ns = coreV1.read_namespace(name="kube-system")
    print("NS: {}".format(ns))

    assert ns.metadata.name == "kube-system", "Wrong namespace given"
