import pytest
import logging

from mirantis.testing.metta import discover, get_environment
from mirantis.testing.metta.plugin import Type

logger = logging.getLogger('chaos-suite')

""" Define our fixtures """


@pytest.fixture(scope='session')
def environment_discover():
    """ discover the metta environments """
    # Tell metta to scan for automatic configuration of itself.
    # It starts my looking in paths upwards for a 'metta.yml' file; if it finds
    # one then it uses that path as a root source of config
    discover()


@pytest.fixture(scope='session')
def environment(environment_discover):
    """ get the metta environment """
    # we don't use the discover fixture, we just need it to run first
    # we don't pass an environment name, which gives us the default environment
    return get_environment()


@pytest.fixture(scope='session')
def environment_up(environment):
    """ get the environment but start the provisioners before returning

    This is preferable to the raw provisioner in cases where you want a running
    cluster so that the cluster startup cost does not get reflected in the
    first test case which uses the fixture.  Also it can tear itself down

    You can still use the provsioners to update the resources if the provisioner
    plugins can handle it.
    """

    launchpad = environment.fixtures.get_plugin(
        type=Type.PROVISIONER, instance_id='launchpad')

    terraform = environment.fixtures.get_plugin(
        type=Type.PROVISIONER, instance_id='terraform')

    # We will use this config to make decisions about what we need to create
    # and destroy for this environment up.
    conf = environment.config.load("config")
    """ somewhat equivalent to reading ./config/config.yml """

    if conf.get("alreadyrunning", default=False):
        logger.info(
            "test infrastructure is aready in place, and does not need to be provisioned.")
    else:
        try:
            logger.info("Preparing the testing cluster using the provisioner")
            terraform.prepare()
        except Exception as e:
            logger.error("Provisioner failed to init: %s", e)
            raise e
        try:
            logger.info(
                "Starting up the testing cluster using the provisioner")
            terraform.apply()
            launchpad.apply()
        except Exception as e:
            logger.error("Provisioner failed to start: %s", e)
            raise e

    yield environment

    if conf.get("keeponfinish", default=False):
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
