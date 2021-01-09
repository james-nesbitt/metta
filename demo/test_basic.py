import os
import docker.models.containers

def test_basic_1(toolbox):
    """ can we get a tooblox """

    # Demo some config retrieval
    prov_config = toolbox.config.load("provisioner")

    assert prov_config.format_string("{_source_:project_config}") == os.path.join(os.getcwd(), "config")
    assert prov_config.format_string("{_source_:project}") == os.getcwd()

def test_check_prov_config(toolbox):
    """ check what the prov config gets us """

    # Demo some config retrieval
    prov_config = toolbox.config.load("provisioner")

    assert prov_config.get("plugin") == "launchpad"

    # Demo some config retrieval
    prov_config = toolbox.config.load("terraform")

    assert prov_config.get("plan.type") == "local"

def test_launchpad_provisioner(toolbox_up):
    """ did we get a good provisioner ? """

    assert True, "Toolbox_Up fixture must have not thrown an error"

def test_launchpad_kubectl_client(toolbox_up):
    """ did we get a good kubectl client """

    kubectl_client = toolbox_up.provisioner().get_client("kubernetes")
    coreV1 = kubectl_client.get_CoreV1Api_client()

    ns = coreV1.read_namespace(name="kube-system")
    print("NS: {}".format(ns))

    assert ns.metadata.name == "kube-system", "Wrong namespace given"

def test_launchpad_docker_client(toolbox_up):
    """ did we get a good docker client ? """

    docker_client = toolbox_up.provisioner().get_client("docker")
    ps = docker_client.containers.list()

    assert len(ps), "No containers were running"
    assert isinstance(ps[0], docker.models.containers.Container), "Did not get a container object from docker list"
