import os
import docker.models.containers

def test_basic_1(config):
    """ can we get a config object with some sane sources """

    # Demo some config retrieval
    prov_config = config.load("provisioner")

    assert prov_config.format_string("{_source_:project_config}") == os.path.join(os.getcwd(), "config")
    assert prov_config.format_string("{_source_:project}") == os.getcwd()

def test_check_prov_config(config):
    """ check what the prov config gets us """

    # Demo some config retrieval
    prov_config = config.load("provisioner")

    assert prov_config.get("plugin") == "launchpad"

    # Demo some config retrieval
    prov_config = config.load("terraform")

    assert prov_config.get("plan.type") == "local"

def test_launchpad_provisioner(provisioner_up):
    """ did we get a good provisioner ? """

    assert True, "Toolbox_Up fixture must have not thrown an error"

def test_launchpad_kubectl_client(provisioner_up):
    """ did we get a good kubectl client """

    kubectl_client = provisioner_up.get_client("kubernetes")
    coreV1 = kubectl_client.get_CoreV1Api_client()

    ns = coreV1.read_namespace(name="kube-system")
    print("NS: {}".format(ns))

    assert ns.metadata.name == "kube-system", "Wrong namespace given"

def test_launchpad_docker_client(provisioner_up):
    """ did we get a good docker client ? """

    docker_client =  provisioner_up.get_client("docker")
    ps = docker_client.containers.list()

    assert len(ps), "No containers were running"
    assert isinstance(ps[0], docker.models.containers.Container), "Did not get a container object from docker list"
