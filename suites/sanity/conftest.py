import pytest
import logging

from uctt import get_environment
from uctt.plugin import Type

# We import constants, but uctt.py actually configures the environment
# for both ptest and the ucttc cli executable.
from .uctt import ENVIRONMENT_NAME

logger = logging.getLogger('mtt ltc demo pytest')

""" Define our fixtures """


@pytest.fixture(scope='session')
def environment():
    """ Create and return the common environment. """
    environment = get_environment(name=ENVIRONMENT_NAME)
    # This environment was defined in ./uctt

    return environment


@pytest.fixture(scope='session')
def provisioner(environment):
    """ Retrieve a provisioner object

    The 'ltc' key matches the provisioner name as defined in the fixtures
    file.  We could just use the first Provisioner plugin, but this is more
    explicit.

    Raises:
    -------

    If this raises a KeyError then we are probably using the wrong name.

    """
    return environment.fixtures.get_plugin(
        type=Type.PROVISIONER, instance_id='combo_provisioner')


@pytest.fixture(scope='session')
def launchpad(environment):
    """ Retrieve the launchpad provisioner

    Raises:
    -------

    If this raises a KeyError then we are probably using the wrong name.

    """
    return environment.fixtures.get_plugin(
        type=Type.PROVISIONER, instance_id='launchpad')


@pytest.fixture(scope='session')
def ansible(environment):
    """ Retrieve the ansible provisioner

    Raises:
    -------

    If this raises a KeyError then we are probably using the wrong name.

    """
    return environment.fixtures.get_plugin(
        type=Type.PROVISIONER, instance_id='ansible')


@pytest.fixture(scope='session')
def terraform(environment):
    """ Retrieve the terraform provisioner

    Raises:
    -------

    If this raises a KeyError then we are probably using the wrong name.

    """
    return environment.fixtures.get_plugin(
        type=Type.PROVISIONER, instance_id='terraform')


@pytest.fixture(scope='session')
def environment_up(environment, terraform, ansible, launchpad):
    """ get the environment but start the provisioners before returning

    This is preferable to the raw provisioner in cases where you want a running
    cluster so that the cluster startup cost does not get reflected in the
    first test case which uses the fixture.  Also it can tear itself down

    You can still use the provsioners to update the resources if the provisioner
    plugins can handle it.
    """

    # We will use
    conf = environment.config.load("config")
    """ somewhat equivalent to reading ./config/config.yml """

    if conf.get("already-running", exception_if_missing=False):
        logger.info(
            "test infrastructure is aready in place, and does not need to be provisioned.")
    else:
        try:
            logger.info("Preparing the testing cluster using the provisioner")
            terraform.prepare()
            ansible.prepare()
        except Exception as e:
            logger.error("Provisioner failed to init: %s", e)
            raise e
        try:
            logger.info(
                "Starting up the testing cluster using the provisioner")
            terraform.apply()
            ansible.apply()
            launchpad.apply()
        except Exception as e:
            logger.error("Provisioner failed to start: %s", e)
            raise e

    yield environment

    if conf.get("keep-on-finish", exception_if_missing=False):
        logger.info("Leaving test infrastructure in place on shutdown")
    else:
        try:
            logger.info(
                "Stopping the test cluster using the provisioner as directed by config")
            terraform.destroy()
        except Exception as e:
            logger.error("Provisioner failed to stop: %s", e)
            raise e
