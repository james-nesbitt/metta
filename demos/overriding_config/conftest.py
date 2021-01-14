import os
import getpass
import logging
import pytest
from datetime import datetime
import mirantis.testing.toolbox

CONFIG_FOLDER = "config"

CONFIG_CLUSTER_FOLDER = "cluster"
OPTIONS_CLUSTER_FLAG = "--cluster"
CLUSTER_DEFAULT = "poc"

CONFIG_SUT_FOLDER = "sut"
OPTIONS_SUT_FLAG = "--sut"
SUT_DEFAULT = "202101"


logging.basicConfig(encoding='utf-8', level=logging.INFO)
logger = logging.getLogger(__file__)

def pytest_addoption(parser):
    parser.addoption(OPTIONS_CLUSTER_FLAG, action="store", default=CLUSTER_DEFAULT)
    parser.addoption(OPTIONS_SUT_FLAG, action="store", default=SUT_DEFAULT)

@pytest.fixture(scope="session")
def sourcelist(request):
    """ Build a sourcelist of config data """
    # find the path to the current folder
    project_path = os.path.dirname(os.path.realpath(__file__))
    project_config_path = os.path.join(project_path, CONFIG_FOLDER)

    sourcelist = mirantis.testing.toolbox.new_sources()
    """ empty config source object """

    sourcelist = mirantis.testing.toolbox.new_sources()

    # use the ./ path as a config source, but mainly for path substitution
    sourcelist.add_filepath_source(project_path, "project")
    # use ./config for config reading
    sourcelist.add_filepath_source(project_config_path, "project_config")

    # Add cluster configuration
    project_config_clusterpath = os.path.join(project_config_path, CONFIG_CLUSTER_FOLDER)
    cluster = request.session.config.getoption(OPTIONS_CLUSTER_FLAG)
    if not os.path.isdir(os.path.join(project_config_clusterpath, cluster)):
        logger.warning("'%s' cluster has no available configuration. PyTest will default to '%s'", cluster, CLUSTER_DEFAULT)
        cluster = CLUSTER_DEFAULT
    sourcelist.add_filepath_source(os.path.join(project_config_clusterpath, cluster), "cluster", 80)

    # Add sut configuration
    project_config_sutpath = os.path.join(project_config_path, CONFIG_SUT_FOLDER)
    sut = request.session.config.getoption(OPTIONS_SUT_FLAG)
    if not os.path.isdir(os.path.join(project_config_sutpath, sut)):
        logger.warning("'%s' sut has no available configuration. PyTest will default to '%s'", sut, SUT_DEFAULT)
        sut = SUT_DEFAULT
    sourcelist.add_filepath_source(os.path.join(project_config_sutpath, sut), "sut", 80)

    # inject some dynamic values into the config system
    additional_config_values = {
        "user": {
            "id": getpass.getuser() # override user id with a host value
        },
        "global": {
            "datetime": datetime.now(), # use a single datetime across all checks
            "sut": sut,
            "cluster": cluster
        }
    }
    # add the dynammic values that we calculated above
    sourcelist.add_dict_source(additional_config_values, "additional", 85)

    return sourcelist

@pytest.fixture(scope="session")
def config(sourcelist):
    """ get an mtt toolbox config object"""
    logger.info("Creating MTT config object")
    return mirantis.testing.toolbox.config_from_source_list(sources=sourcelist)


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
        provisioner.prepare()
        provisioner.up()
    except Exception as e:
        logger.error("Provisioner failed to start: %s", e)
        raise

    yield provisioner

    if conf.get("destroy-on-finish", exception_if_missing=False):
        logger.info("Stopping the test cluster using the provisioner as directed by config")
        provisioner.down()
    else:
        logger.info("Leaving test infrastructure in place on shutdown")
