import pytest
import logging

from mirantis.testing.metta import get_environment
from mirantis.testing.metta.plugin import Type

# We import constants, but metta.py actually configures the environment
# for both ptest and the mettac cli executable.
from .metta import ENVIRONMENT_NAME_BEFORE, ENVIRONMENT_NAME_AFTER

logger = logging.getLogger('metta ltc demo pytest')

""" Define our fixtures """


@pytest.fixture()
def environment_before():
    """ Create and return the first environment. """
    environment = get_environment(name=ENVIRONMENT_NAME_BEFORE)
    # This environment was defined in ./metta

    return environment

@pytest.fixture()
def environment_before():
    """ Create and return the second environment. """
    environment = get_environment(name=ENVIRONMENT_NAME_AFTER)
    # This environment was defined in ./metta

    return environment


@pytest.fixture(scope='session')
def launchpad(environment):
    """ Retrieve the launchpad provisioner

    Raises:
    -------

    If this raises a KeyError then we are probably using the wrong name.

    """
    launchpad = environment.fixtures.get_plugin(
        type=Type.PROVISIONER, instance_id='launchpad')

    ansible = environment.fixtures.get_plugin(
        type=Type.PROVISIONER, instance_id='ansible')

    terraform = environment.fixtures.get_plugin(
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

    # We will use this config to make decisions about what we need to create
    # and destroy for this environment up.
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
            launchpad.destroy()
            terraform.destroy()
        except Exception as e:
            logger.error("Provisioner failed to stop: %s", e)
            raise e
