
import os
import logging
import pytest
import mirantis.testing.toolbox

CONFIG_FOLDER = "config"

logging.basicConfig(encoding='utf-8', level=logging.INFO)
logger = logging.getLogger(__file__)

@pytest.fixture(scope="session")
def config():
    """ get an mtt toolbox config object"""
    logger.debug("Creating a new toolbox fixture")
    project_path = os.path.dirname(os.path.realpath(__file__))

    conf_sources = mirantis.testing.toolbox.new_sources()
    """ empty config source object """
    conf_sources.add_filepath_source(os.path.join(project_path, CONFIG_FOLDER), "project_config")
    """ designate the `./config` path as a source of file configs """

    logger.info("Creating MTT config object")
    return mirantis.testing.toolbox.config_from_source_list(sources=conf_sources)

@pytest.fixture(scope="session")
def provisioner(config):
    """ get a provisioner based on the config """
    return mirantis.testing.toolbox.provisioner_from_config(config)


def test_config(config):
    """ Show how the config object works

    Just shows some simple retrieves, although it doesn't show any of the
    overriding or templating features.

    """

    demo_config = config.load("demo") # load and merge all demo.yml|json files

    assert demo_config.get("name") == "myname"
    assert demo_config.get("settings.one") == "1"

def test_provisioner(provisioner):
    """ show how you would use the provisioner

    the provisioner.yml file configures our provisioner to be the "dummy" plugin
    which doesn't actually do anything, but this shows how you could do it.

    You probably want to `up()` the provisioner in the fixture instead of here
    so that the time spent bringing up/down the cluster isn't reflected in the
    test.

    """

    provisioner.prepare()
    provisioner.up()

    assert True, "This will never fail"

    provisioner.down()
