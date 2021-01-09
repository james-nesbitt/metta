"""

Dummy test suite for testing out MKE/MSR clusters

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
def toolbox():
    """ get an mtt toolbox """
    logger.debug("Creating a new toolbox fixture")
    project_path = os.path.dirname(os.path.realpath(__file__))

    conf_sources = mirantis.testing.toolbox.new_sources()
    conf_sources.add_filepath_source(project_path, "project")
    conf_sources.add_filepath_source(os.path.join(project_path, CONFIG_FOLDER), "project_config")
    logger.info("Creating MTT toolbox object")

    additional_config_values = {
        "user": {
            "id": getpass.getuser()
        }
    }

    return mirantis.testing.toolbox.toolbox_from_settings(conf_sources=conf_sources, additional_config_values=additional_config_values)

@pytest.fixture(scope="session")
def toolbox_up(toolbox):
    """ get the toolbox but start the provisioner before returning

    This is preferable to the raw toolbox in cases where you want a running
    cluster because the cluster startup cost does not get reflected in the
    first test case which uses the fixture.  Also it can tear itself down
    """
    logger.info("Running MTT provisioner up()")

    conf = toolbox.config.load("config")

    try:
        logger.info("Starting up the testing cluster using the toolbox")
        toolbox.provisioner().up()
    except Exception as e:
        logger.error("Provisioner failed to start: %s", e)
        raise

    yield toolbox

    if conf.get("options.destroy-on-finish", exception_if_missing=False):
        logger.info("Stopping the test cluster using the toolbox as directoed by config")
        toolbox.provisioner().down()
    else:
        logger.info("Leaving test infrastructure in place on shutdown")
