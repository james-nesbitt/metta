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

from mirantis.testing.metta_launchpad.provisioner import (
    METTA_LAUNCHPAD_PROVISIONER_PLUGIN_ID,
)
from mirantis.testing.metta_terraform.provisioner import (
    METTA_TERRAFORM_PROVISIONER_PLUGIN_ID,
)

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


# Consumer fixtures

# Here are the two fixtures that you can use to get access to the environment
# object in its default state, and in its "after" state.  Both of the following
# fixtures return that same environment object, but the before fixture has run
# the full provisioning of the environment in its default state, and the after
# fixture has run the upgrade on the after state.
#
# @NOTE IT is up to the consumer to confirm that you run all tests that need
#   the "before" state before you run any of the "after" state.  If you run
#   a before test after an after test, you will receive an environment object
#   that is in the wrong state.


@pytest.fixture(scope="session")
def environment_before_up(environment) -> Environment:
    """get the metta environment"""
    # apply the environment in it's default state
    environment_up(environment)
    return environment


@pytest.fixture(scope="session")
def environment_after_up(environment) -> Environment:
    """get the metta environment upgraded in its after state"""
    environment.set_state("after")
    environment_upgrade(environment)
    yield environment
    environment_down(environment)


# Environment utility methods


def environment_up(environment) -> Environment:
    """bring up the passed environment"""

    launchpad = environment.fixtures.get_plugin(
        interfaces=[METTA_PLUGIN_INTERFACE_ROLE_PROVISIONER],
        plugin_id=METTA_LAUNCHPAD_PROVISIONER_PLUGIN_ID,
    )

    terraform = environment.fixtures.get_plugin(
        interfaces=[METTA_PLUGIN_INTERFACE_ROLE_PROVISIONER],
        plugin_id=METTA_TERRAFORM_PROVISIONER_PLUGIN_ID,
    )

    # We will use this config to make decisions about what we need to create
    # and destroy for this environment up.
    conf = environment.config.load("config")
    """ somewhat equivalent to reading ./config/config.yml """

    if conf.get("alreadyrunning", default=False):
        logger.info("test infrastructure is aready in place, and does not need to be provisioned.")
    else:
        try:
            logger.info("Preparing the testing cluster using the provisioner")
            terraform.prepare()
        except Exception as err:
            logger.error("Provisioner failed to init: %s", err)
            raise err
        try:
            logger.info("Starting up the testing cluster using the provisioner")
            terraform.apply()
            launchpad.apply()
        except Exception as err:
            logger.error("Provisioner failed to start: %s", err)
            raise err

    # return the environment
    return environment


def environment_upgrade(environment):
    """upgrade up the passed environment

    In this process we only apply launchpad to save time and also in case the
    terraform chart is not actually declarative safe for an upgrade where it is
    not actually changed.  This occurs under some circumstances in the spot
    requests.

    """
    # We will use this config to make decisions about what we need to create
    # and destroy for this environment up.
    conf = environment.config.load("config")
    """ somewhat equivalent to reading ./config/config.yml """

    launchpad = environment.fixtures.get_plugin(
        interfaces=[METTA_PLUGIN_INTERFACE_ROLE_PROVISIONER],
        plugin_id=METTA_LAUNCHPAD_PROVISIONER_PLUGIN_ID,
    )
    """ launchpad provisioner object """

    if conf.get("alreadyrunning", default=False):
        logger.info("test infrastructure is aready in place, and does not need to be provisioned.")
    else:
        try:
            logger.info(
                "Preparing the testing cluster for upgrade using the launchpad provisioner only"
            )
            launchpad.prepare()
        except Exception as err:
            logger.error("Provisioner failed to init: %s", err)
            raise err
        try:
            logger.info("Upgrading up the testing cluster using the launchpad provisioner")
            launchpad.apply()
        except Exception as err:
            logger.error("Launchpad provisioner failed to apply: %s", err)
            raise err


def environment_down(environment):
    """tear down an environment"""

    # We will use this config to make decisions about what we need to create
    # and destroy for this environment up.
    conf = environment.config.load("config")
    """ somewhat equivalent to reading ./config/config.yml """

    launchpad = environment.fixtures.get_plugin(
        interfaces=[METTA_PLUGIN_INTERFACE_ROLE_PROVISIONER],
        plugin_id=METTA_LAUNCHPAD_PROVISIONER_PLUGIN_ID,
    )

    terraform = environment.fixtures.get_plugin(
        interfaces=[METTA_PLUGIN_INTERFACE_ROLE_PROVISIONER],
        plugin_id=METTA_TERRAFORM_PROVISIONER_PLUGIN_ID,
    )

    if conf.get("keepwhenfinish", default=False):
        logger.info("Leaving test infrastructure in place on shutdown")
    else:
        try:
            logger.info("Stopping the test cluster using the provisioner as directed by config")
            launchpad.destroy()
            terraform.destroy()
        except Exception as err:
            logger.error("Provisioner failed to stop: %s", err)
            raise err
