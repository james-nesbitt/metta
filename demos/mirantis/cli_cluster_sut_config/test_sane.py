
def test_options(config):
    """ Can we get a config """

    global_config = config.load("global")
    print("CLUSTER:{}".format(global_config.get("cluster")))
    print("SUT:{}".format(global_config.get("sut")))

    terraform_config = config.load("terraform")
    print("TF_VARS:{}".format(terraform_config.get("vars")))

def test_provisioner(provisioner_up):
    """ Can we get a running provisioner """

    print("CLUSTER_NAME:{}".format(provisioner_up.output("cluster_name")))
    print("MKE_CLUSTER_YAML: \n{}".format(provisioner_up.output("mke_cluster_yaml")))
