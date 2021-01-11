"""

Demo test suite for testing out MKE/MSR clusters

"""
import getpass
import os
import logging
import pytest
import mirantis.testing.toolbox
from mirantis.testing.toolbox.config import Config

CONFIG_FOLDER = "config"

logging.basicConfig(encoding='utf-8', level=logging.INFO)
logger = logging.getLogger(__file__)

@pytest.fixture(scope="session")
def config():
    """ get an mtt config object """
    logger.debug("Creating a new toolbox fixture")
    project_path = os.path.dirname(os.path.realpath(__file__))

    additional_config_values = {
        "user": {
            "id": getpass.getuser()
        }
    }

    conf_sources = mirantis.testing.toolbox.new_sources()
    conf_sources.add_filepath_source(project_path, "project")
    conf_sources.add_filepath_source(os.path.join(project_path, CONFIG_FOLDER), "project_config")
    conf_sources.add_dict_source(additional_config_values, "additional", 80)

    logger.info("Creating MTT config object")
    return mirantis.testing.toolbox.config_from_source_list(sources=conf_sources)

@pytest.fixture(scope="session")
def provisioner(config):
    """ get a provisioner based on the config """
    return mirantis.testing.toolbox.provisioner_from_config(config)

@pytest.fixture(scope="session")
def provisioner_up(config, provisioner):
    """ get the provisioner but start the provisioner before returning

    This is preferable to the raw provisioner in cases where you want a running
    cluster because the cluster startup cost does not get reflected in the
    first test case which uses the fixture.  Also it can tear itself down
    """
    logger.info("Running MTT provisioner up()")

    conf = config.load("config")

    try:
        logger.info("Starting up the testing cluster using the provisioner")
        provisioner.up()
    except Exception as e:
        logger.error("Provisioner failed to start: %s", e)
        raise

    yield provisioner

    if conf.get("options.destroy-on-finish", exception_if_missing=False):
        logger.info("Stopping the test cluster using the provisioner as directed by config")
        provisioner.down()
    else:
        logger.info("Leaving test infrastructure in place on shutdown")
