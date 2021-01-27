import logging
import pytest
import pathlib
import getpass
from datetime import datetime
import os.path

logging.basicConfig(encoding='utf-8', level=logging.INFO)
logger = logging.getLogger('mtt ltc demo')

DIR = str(pathlib.Path(__file__).parent.absolute())
""" Absolute path to this file, used as a root path """

# Import the mtt core
import mirantis.testing.mtt as mtt
# Import packages that we use
# 1. this import some functions that we use
# 2. this activates the module decorators, which registers plugins
import mirantis.testing.mtt_common as mtt_common
# we are going to use a terraform plan fro this module
import mirantis.testing.mtt_mirantis as mtt_mirantis
# this will give us access to the terraform provisioner
import mirantis.testing.mtt_terraform as mtt_terraform

# Defaults / keys related to cli options

CONFIG_FOLDER = "config"

CONFIG_CLUSTER_FOLDER = "cluster"
OPTIONS_CLUSTER_FLAG = "--cluster"
CLUSTER_DEFAULT = "poc"

CONFIG_SUT_FOLDER = "sut"
OPTIONS_SUT_FLAG = "--sut"
SUT_DEFAULT = "202101"

def pytest_addoption(parser):
    """ Add pytest cli options to allow --sut and --cluster """
    parser.addoption(OPTIONS_CLUSTER_FLAG, action="store", default=CLUSTER_DEFAULT)
    parser.addoption(OPTIONS_SUT_FLAG, action="store", default=SUT_DEFAULT)

@pytest.fixture(scope='session')
def config(request):
    """

    Create a config object.

    We add sources for:
    - our own ./config
    - some dynamic overrides pulled from cli options
    - whichever --sut / --cluster (or defaults) where chosend

    """

    project_config_path = os.path.join(DIR, CONFIG_FOLDER)

    config = mtt.new_config()
    # Add our ./config path as a config source
    config.add_source(mtt_common.MTT_PLUGIN_ID_CONFIGSOURCE_PATH, 'project_config').set_path(project_config_path)

    # Add cluster configuration from cli option
    project_config_clusterpath = os.path.join(project_config_path, CONFIG_CLUSTER_FOLDER)
    cluster = request.session.config.getoption(OPTIONS_CLUSTER_FLAG)
    if not os.path.isdir(os.path.join(project_config_clusterpath, cluster)):
        logger.warning("'%s' cluster has no available configuration. PyTest will default to '%s'", cluster, CLUSTER_DEFAULT)
        cluster = CLUSTER_DEFAULT
    config.add_source(mtt_common.MTT_PLUGIN_ID_CONFIGSOURCE_PATH, 'cluster', priority=80).set_path(os.path.join(project_config_clusterpath, cluster))

    # Add sut configuration from cli option
    project_config_sutpath = os.path.join(project_config_path, CONFIG_SUT_FOLDER)
    sut = request.session.config.getoption(OPTIONS_SUT_FLAG)
    if not os.path.isdir(os.path.join(project_config_sutpath, sut)):
        logger.warning("'%s' sut has no available configuration. PyTest will default to '%s'", sut, SUT_DEFAULT)
        sut = SUT_DEFAULT
    config.add_source(mtt_common.MTT_PLUGIN_ID_CONFIGSOURCE_PATH, 'sut', priority=80).set_path(os.path.join(project_config_sutpath, sut))

    # Add some dymanic values for config
    config.add_source(mtt_common.MTT_PLUGIN_ID_CONFIGSOURCE_DICT, 'dynamic').set_data({
        "user": {
            "id": getpass.getuser() # override user id with a host value
        },
        "global": {
            "datetime": datetime.now(), # use a single datetime across all checks
        },
        "global": {
            "datetime": datetime.now(), # use a single datetime across all checks
            "sut": sut,
            "cluster": cluster
        },
        config.paths_label(): { # special config label for file paths, usually just 'paths'
            "project": DIR  # you can use 'paths:project' in config to substitute this path
        }
    })

    # this can do a lot of things, but we are only using it to access the
    # terraform plan in this module
    mtt_mirantis.config_interpret_mtt_mirantis(config)

    return config

@pytest.fixture(scope="session")
def provisioner(config):
    """ get a provisioner based on the config """
    return mtt.new_provisioner_from_config(config)

@pytest.fixture(scope='session')
def provisioner_up(config, provisioner):
    """ get the provisioner but start the provisioner before returning

    This is preferable to the raw provisioner in cases where you want a running
    cluster so that the cluster startup cost does not get reflected in the
    first test case which uses the fixture.  Also it can tear itself down

    You can still use provisioner.apply() update the resources if the provisioner
    can handle it.
    """
    logger.info("Running MTT provisioner up()")

    conf = config.load("config")

    try:
        logger.info("Preparing the testing cluster using the provisioner")
        provisioner.prepare()
    except Exception as e:
        logger.error("Provisioner failed to init: %s", e)
        raise e
    try:
        logger.info("Starting up the testing cluster using the provisioner")
        provisioner.apply()
    except Exception as e:
        logger.error("Provisioner failed to start: %s", e)
        raise e

    yield provisioner

    if conf.get("destroy-on-finish", exception_if_missing=False):
        try:
            logger.info("Stopping the test cluster using the provisioner as directed by config")
            provisioner.destroy()
        except Exception as e:
            logger.error("Provisioner failed to stop: %s", e)
            raise e
    else:
        logger.info("Leaving test infrastructure in place on shutdown")
