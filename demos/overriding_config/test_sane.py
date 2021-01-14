
def test_options(sourcelist, config, provisioner_up):
    """ Can we get a config """

    ordered_sources = [(element.key, element.priority, element.handler.name()) for element in sourcelist.get_ordered_sources()]
    global_config = config.load("global")
    terraform_config = config.load("terraform")

    print("CLUSTER:{}".format(global_config.get("cluster")))
    print("SUT:{}".format(global_config.get("sut")))
    print("TF_VARS:{}".format(terraform_config.get("vars")))
    print("CLUSTER_NAME:{}".format(provisioner_up.output("cluster_name")))
