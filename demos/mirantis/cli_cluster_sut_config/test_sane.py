
def test_options(config):
    """ Can we get the expected config """

    global_config = config.load("global")
    print("CLUSTER:{}".format(global_config.get("cluster")))
    print("SUT:{}".format(global_config.get("sut")))

    tf_config = config.load("terraform")
    print("TF_VARS:{}".format(tf_config.get("vars")))

def test_provisioner(provisioner_up):
    """ Can we get a running provisioner """

    # for outputs, the provisioner plugin must recognize the key
    print("CLUSTER_NAME:{}".format(provisioner_up.get_output("cluster_name")))
    print("MKE_CLUSTER_YAML: \n{}".format(provisioner_up.get_output("mke_cluster_yaml")))
