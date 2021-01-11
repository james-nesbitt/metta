import os

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
