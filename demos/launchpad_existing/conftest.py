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
    """ get a provisioner based on the config

    Create the provisioner, and then prepare() and up() it.
    """
    provisioner = mirantis.testing.toolbox.provisioner_from_config(config)

    provisioner.prepare()
    provisioner.up()

    yield provisioner

    provisioner.down()
