import pytest
import logging

from mirantis.testing.metta import discover, get_environment
from mirantis.testing.metta.plugin import Type

logger = logging.getLogger('upgrade-suite')

""" Define our fixtures """


@pytest.fixture(scope='session')
def environment_discover():
    """ discover the metta environments """
    # Tell metta to scan for automatic configuration of itself.
    # It starts my looking in paths upwards for a 'metta.yml' file; if it finds
    # one then it uses that path as a root source of config
    discover()


# Track which environment is currently UP
current_up_environment = ''


@pytest.fixture()
def environment_before_up(environment_discover):
    """ get the metta environment """
    # we don't use the discover fixture, we just need it to run first
    # we don't pass an environment name, which gives us the default environment
    env = get_environment('before')
    environment_up(env)
    return env


@pytest.fixture()
def environment_after_up(environment_discover):
    """ get the metta environment """
    # we don't use the discover fixture, we just need it to run first
    # we don't pass an environment name, which gives us the default environment
    env = get_environment('after')
    environment_up(env)
    return env


""" Cleanup """


def pytest_unconfigure(config):
    """ Tear down any existing clusters """

    if current_up_environment:
        env = get_environment(current_up_environment)
        environment_down(env)


""" Environment utility methods """


def environment_up(environment):
    """ bring up the passed environment """
    global current_up_environment

    # If this environment is already up, then skip
    if environment.name == current_up_environment:
        return

    # We will use this config to make decisions about what we need to create
    # and destroy for this environment up.
    conf = environment.config.load("config")
    """ somewhat equivalent to reading ./config/config.yml """

    launchpad = environment.fixtures.get_plugin(
        type=Type.PROVISIONER, instance_id='launchpad')

    ansible = environment.fixtures.get_plugin(
        type=Type.PROVISIONER, instance_id='ansible')

    terraform = environment.fixtures.get_plugin(
        type=Type.PROVISIONER, instance_id='terraform')

    if conf.get("alreadyrunning", exception_if_missing=False):
        logger.info(
            "test infrastructure is aready in place, and does not need to be provisioned.")
        current_up_environment = environment.name
    else:
        try:
            logger.info("Preparing the testing cluster using the provisioner")
            terraform.prepare()
            ansible.prepare()
            launchpad.prepare()
        except Exception as e:
            logger.error("Provisioner failed to init: %s", e)
            raise e
        try:
            logger.info(
                "Starting up the testing cluster using the provisioner")
            terraform.apply()
            ansible.apply()
            launchpad.apply()

            """ Set the env as current """
            current_up_environment = environment.name
        except Exception as e:
            logger.error("Provisioner failed to start: %s", e)
            raise e


def environment_down(environment):
    """ tear down an environment if it is currently up """
    global current_up_environment

    # If this environment is already up, then skip
    if not environment.name == current_up_environment:
        return

    # We will use this config to make decisions about what we need to create
    # and destroy for this environment up.
    conf = environment.config.load("config")
    """ somewhat equivalent to reading ./config/config.yml """

    launchpad = environment.fixtures.get_plugin(
        type=Type.PROVISIONER, instance_id='launchpad')

    ansible = environment.fixtures.get_plugin(
        type=Type.PROVISIONER, instance_id='ansible')

    terraform = environment.fixtures.get_plugin(
        type=Type.PROVISIONER, instance_id='terraform')

    if conf.get("keepwhenfinish", exception_if_missing=False):
        logger.info("Leaving test infrastructure in place on shutdown")
        current_up_environment = ''
    else:
        try:
            logger.info(
                "Stopping the test cluster using the provisioner as directed by config")
            launchpad.destroy()
            ansible.destroy()
            terraform.destroy()

            """ Unset the env as current """
            current_up_environment = ''
        except Exception as e:
            logger.error("Provisioner failed to stop: %s", e)
            raise e
