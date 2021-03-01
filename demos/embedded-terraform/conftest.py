import pytest
import logging
import os.path

from mirantis.testing.metta import discover, get_environment
from mirantis.testing.metta.plugin import Type

logger = logging.getLogger('metta-embedded-tf')

""" Define our fixtures """


@pytest.fixture(scope='session')
def environment_discover():
    """ discover the metta environment s"""
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
def launchpad(environment):
    """ Retrieve the launchpad provisioner

    This loads the environment provisioner plugin which was created in the
    environment by scanning the ./config/fixtures.yml file.

    Raises:
    -------

    If this raises a KeyError then we are probably using the wrong name.

    """
    return environment.fixtures.get_plugin(
        type=Type.PROVISIONER, instance_id='launchpad')


@pytest.fixture(scope='session')
def ansible(environment):
    """ Retrieve the ansible provisioner

    This loads the environment provisioner plugin which was created in the
    environment by scanning the ./config/fixtures.yml file.

    The Ansible plugin is currently empty.

    Raises:
    -------

    If this raises a KeyError then we are probably using the wrong name.

    """
    return environment.fixtures.get_plugin(
        type=Type.PROVISIONER, instance_id='ansible')


@pytest.fixture(scope='session')
def terraform(environment):
    """ Retrieve the terraform provisioner

    This loads the environment provisioner plugin which was created in the
    environment by scanning the ./config/fixtures.yml file.

    Raises:
    -------

    If this raises a KeyError then we are probably using the wrong name.

    """
    return environment.fixtures.get_plugin(
        type=Type.PROVISIONER, instance_id='terraform')


@pytest.fixture(scope='session')
def environment_up(environment, terraform, ansible, launchpad):
    """ get the environment but start the provisioners before returning

    This is preferable to the raw environment in cases where you want a running
    cluster so that the cluster startup cost does not get reflected in the
    first test case which uses the fixture.  Also it can tear itself down

    You can still use the provsioners to update cluster resources during a test.

    """

    try:
        logger.info("Preparing the testing cluster using the provisioners")
        terraform.prepare()
        ansible.prepare()
    except Exception as e:
        logger.error("Provisioner failed to init: %s", e)
        raise e
    try:
        logger.info("Starting up the testing cluster using the provisioners")
        terraform.apply()
        ansible.apply()
        launchpad.apply()
    except Exception as e:
        logger.error("Provisioner failed to start: %s", e)
        raise e

    yield environment

    try:
        logger.info(
            "Stopping the test cluster using the provisioners")
        launchpad.destroy()
        terraform.destroy()
    except Exception as e:
        logger.error("Provisioner failed to stop: %s", e)
        raise e
