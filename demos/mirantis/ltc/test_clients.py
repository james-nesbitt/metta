"""

Test that some clients work

"""

import logging
import docker.models.containers

logger = logging.getLogger("test_clients")

def test_paths(config, dir):

    assert config.load('paths').get('project') == dir
    assert config.load('variables').get('files_path') == dir
    assert config.load('config').format_string("{paths:project}") == dir
    assert config.load('config').format_string("{variables:files_path}") == dir
    assert config.load('config').format_string("{variables:files_path?.}") == dir

def test_launchpad_kubectl_client(provisioner_up):
    """ did we get a good kubectl client """

    logger.info("Getting K8s client")
    kubectl_client = provisioner_up.get_client("mtt_kubernetes")

    coreV1 = kubectl_client.get_CoreV1Api_client()
    ns = coreV1.read_namespace(name="kube-system")
    print("NS: {}".format(ns))

    assert ns.metadata.name == "kube-system", "Wrong namespace given"

def test_launchpad_docker_client(provisioner_up):
    """ did we get a good docker client ? """

    logger.info("Getting docker client")
    docker_client =  provisioner_up.get_client("mtt_docker")

    ps = docker_client.containers.list()

    assert len(ps), "No containers were running.  We expected at least the MKE containers"
    assert isinstance(ps[0], docker.models.containers.Container), "Did not get a container object from docker list"
