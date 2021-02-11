# -- Set ./ as a module load path
import fixtures
import pytest
import logging
import os
import sys
dir_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(dir_path)
# --------------------------------


logger = logging.getLogger('mtt ltc demo pytest')

# Import the mtt core

""" Define our fixtures """


@pytest.fixture(scope='session')
def config():
    """ Create a config object. """
    return fixtures.config()


@pytest.fixture(scope='session')
def provisioner(config):
    """ Retrieve a provisioner object """
    return fixtures.provisioner(config=config, instance_id='ltc_provisioner')


@pytest.fixture(scope='session')
def provisioner_up(config, provisioner):
    """ get the provisioner but start the provisioner before returning

    This is preferable to the raw provisioner in cases where you want a running
    cluster so that the cluster startup cost does not get reflected in the
    first test case which uses the fixture.  Also it can tear itself down

    You can still use provisioner.apply() update the resources if the provisioner
    can handle it.
    """

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

    if conf.get("keep-on-finish", exception_if_missing=False):
        logger.info("Leaving test infrastructure in place on shutdown")
    else:
        try:
            logger.info(
                "Stopping the test cluster using the provisioner as directed by config")
            provisioner.destroy()
        except Exception as e:
            logger.error("Provisioner failed to stop: %s", e)
            raise e
