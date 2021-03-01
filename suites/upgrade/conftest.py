import pytest
import logging

from mirantis.testing.metta import get_environment
from mirantis.testing.metta.plugin import Type

<<<<<<< Updated upstream
# We import constants, but metta.py actually configures the environment
# for both ptest and the mettac cli executable.
from .metta import ENVIRONMENT_NAME_BEFORE, ENVIRONMENT_NAME_AFTER

logger = logging.getLogger('metta ltc demo pytest')
=======
logger = logging.getLogger('upgrade-suite')
>>>>>>> Stashed changes

""" Define our fixtures """


@pytest.fixture(scope='session')
def environment_discover():
    """ discover the metta environments """
    # Tell metta to scan for automatic configuration of itself.
    # It starts my looking in paths upwards for a 'metta.yml' file; if it finds
    # one then it uses that path as a root source of config
    new_environments_from_discover()


@pytest.fixture(scope='session')
def environment(environment_discover):
    """ get the metta environment """
    # we don't use the discover fixture, we just need it to run first
    # we don't pass an environment name, which gives us the default environment
    return get_environment()

@pytest.fixture(scope="")
dev phase_handler(environment_discover):
    pass

class PhaseHandler:

    def __init__(environment, phases):
        self.environment = environment
        self.environment_config = environment.config
        self.phases = phases
        self.active_phase = -1

<<<<<<< Updated upstream
@pytest.fixture()
def environment_before():
    """ Create and return the second environment. """
    environment = get_environment(name=ENVIRONMENT_NAME_AFTER)
    # This environment was defined in ./metta
=======
    def get_environment(self):
        return self.environment

    def phase_bump(self, delta = 1):
        new_active_phase = self.active_phase + delta
        if new_active_phase < 0 or new_active_phase >= len(self.phases)
            raise ValueError("Tried to bump to a phase that doesn't exist")
>>>>>>> Stashed changes



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
