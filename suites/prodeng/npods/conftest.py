"""

PyTest setup for test suite

Primarily used to define fixtures used for the pytest implementation, which are then consumed by
the test cases themselved.

We realy heavily on metta discovery which looks for the metta.yml file, and uses that to interpret
the config folder to define metta infrastructure.  The same approach is used by the metta cli,
which makes the cli quite usable in this scope

"""
import logging

import pytest

from mirantis.testing.metta import discover, get_environment, Environment
from mirantis.testing.metta.provisioner import METTA_PLUGIN_INTERFACE_ROLE_PROVISIONER


logger = logging.getLogger("pytest-conftest")

""" Define our fixtures """

# impossible to chain pytest fixtures without using the same names
# pylint: disable=redefined-outer-name
# unused argument is their to force dependency hierarchy
# pylint: disable=unused-argument


@pytest.fixture(scope="session")
def environment_discover():
    """discover the metta environments"""
    # Tell metta to scan for automatic configuration of itself.
    # It starts my looking in paths upwards for a 'metta.yml' file; if it finds
    # one then it uses that path as a root source of config
    discover()


@pytest.fixture(scope="session")
def environment(environment_discover) -> Environment:
    """get the metta environment"""
    # we don't use the discover fixture, we just need it to run first
    # we don't pass an environment name, which gives us the default environment
    return get_environment()


@pytest.fixture(scope="session")
def provisioner(environment) -> object:
    """Get the provisioner plugin."""
    return environment.fixtures.get_plugin(
        interfaces=[METTA_PLUGIN_INTERFACE_ROLE_PROVISIONER]
    )


@pytest.fixture(scope="session")
def environment_up(environment, provisioner) -> Environment:
    """get the environment but start the provisioners before returning

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

    if conf.get("alreadyrunning", default=False):
        logger.info(
            "test infrastructure is aready in place, and does not need to be provisioned."
        )
    else:
        try:
            logger.info("Preparing the testing cluster using the provisioner")
            provisioner.prepare()
        except Exception as err:
            logger.error("Provisioner failed to init: %s", err)
            raise err
        try:
            logger.info("Starting up the testing cluster using the provisioner")
            provisioner.apply()
        except Exception as err:
            logger.error("Provisioner failed to start: %s", err)
            raise err

    # yield the environment, and all following functionality will be used for teardown.
    yield environment

    if conf.get("keeponfinish", default=False):
        logger.info("Leaving test infrastructure in place on shutdown")
    else:
        try:
            logger.info(
                "Stopping the test cluster using the provisioner as directed by config"
            )
            provisioner.destroy()
        except Exception as err:
            logger.error("Provisioner failed to stop: %s", err)
            raise err
