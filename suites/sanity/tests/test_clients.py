"""

Test that some clients work

"""

import logging

import docker.models.containers
from uctt.contrib.docker import UCTT_PLUGIN_ID_DOCKER_CLIENT
from uctt.contrib.kubernetes import UCTT_PLUGIN_ID_KUBERNETES_CLIENT

logger = logging.getLogger("test_clients")


def test_launchpad_kubectl_client(provisioner_up):
    """ did we get a good kubectl client """

    logger.info("Getting K8s client")
    kubectl_client = provisioner_up.get_client(
        plugin_id=UCTT_PLUGIN_ID_KUBERNETES_CLIENT)

    coreV1 = kubectl_client.get_CoreV1Api_client()
    ns = coreV1.read_namespace(name="kube-system")
    print("NS: {}".format(ns))

    assert ns.metadata.name == "kube-system", "Wrong namespace given"


def test_launchpad_docker_client(provisioner_up):
    """ did we get a good docker client ? """

    logger.info("Getting docker client")
    docker_client = provisioner_up.get_client(
        plugin_id=UCTT_PLUGIN_ID_DOCKER_CLIENT)

    ps = docker_client.containers.list()

    assert len(
        ps), "No containers were running.  We expected at least the MKE containers"
    assert isinstance(
        ps[0], docker.models.containers.Container), "Did not get a container object from docker list"
