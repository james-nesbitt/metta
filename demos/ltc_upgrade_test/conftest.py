import mirantis.testing.mtt_terraform as mtt_terraform
import mirantis.testing.mtt_common as mtt_common
import mirantis.testing.mtt as mtt
import logging
import pytest
import pathlib
import getpass
from datetime import datetime
import os.path

logger = logging.getLogger('mtt ltc demo')

DIR = str(pathlib.Path(__file__).parent.absolute())
""" Absolute path to this file, used as a root path """

# Import the mtt core
# Import packages that we use
# 1. this import some functions that we use
# 2. this activates the module decorators, which registers plugins
# mtt also import mtt_kubernetes and mtt_docker

""" Define our fixtures """


@pytest.fixture(scope='session')
def dir():
    """ quick access to project root path """
    return DIR


@pytest.fixture(scope='session')
def config():
    """

    Create a config object.

    We add sources for:
    - our own ./config
    - some dynamic overrides
    - we let mtt_common add some common paths
    - we let mtt interpet variation and release from its config

    """

    config = mtt.new_config()
    # Add our ./config path as a config source
    config.add_source(
        mtt_common.MTT_PLUGIN_ID_SOURCE_PATH,
        'project_config').set_path(
        os.path.join(
            DIR,
            'config'))
    # Add some dymanic values for config
    config.add_source(mtt_common.MTT_PLUGIN_ID_SOURCE_DICT, 'project_dynamic').set_data({
        "user": {
            "id": getpass.getuser()  # override user id with a host value
        },
        "global": {
            "datetime": datetime.now(),  # use a single datetime across all checks
        },
        config.paths_label(): {  # special config label for file paths, usually just 'paths'
            "project": DIR  # you can use 'paths:project' in config to substitute this path
        }
    })

    # adds user and mtt_common defaults
    mtt_common.add_common_config(config)
    # let mtt interpret stuff from the mtt config
    mtt.config_interpret_mtt(config)
    # of primary value is that mtt can interpret ./config/mtt
    # to determing a cluster, variation and release, which adds more config from
    # that module.

    return config


@pytest.fixture(scope='session')
def provisioner(config):
    """ Retrieve a provisioner object

    we only use one provisioned cluster in this test suite
    (but we still give it an arbitraty name)

    Use this if your test-cases want unprovisioned resources, but then they
    need to manage startup and teardown themselves.

    @see provisioner_up

    """
    return mtt.new_provisioner_from_config(config, 'ltc_provisioner')


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
            logger.info(
                "Stopping the test cluster using the provisioner as directed by config")
            provisioner.destroy()
        except Exception as e:
            logger.error("Provisioner failed to stop: %s", e)
            raise e
    else:
        logger.info("Leaving test infrastructure in place on shutdown")
