"""

PyTest fixtures for upgrade testing.

"""
import logging

import pytest

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.fixture import Fixtures
from mirantis.testing.metta.provisioner import METTA_PLUGIN_INTERFACE_ROLE_PROVISIONER
from mirantis.testing.metta.workload import METTA_PLUGIN_INTERFACE_ROLE_WORKLOAD
from mirantis.testing.metta_health.healthpoll_workload import (
    HealthPollWorkload,
    METTA_PLUGIN_ID_WORKLOAD_HEALTHPOLL,
)

from mirantis.testing.metta_launchpad.provisioner import (
    METTA_LAUNCHPAD_PROVISIONER_PLUGIN_ID,
)
from mirantis.testing.metta_terraform.provisioner import (
    METTA_TERRAFORM_PROVISIONER_PLUGIN_ID,
)

logger = logging.getLogger("upgrade.conftest")

# impossible to chain pytest fixtures without using the same names
# pylint: disable=redefined-outer-name
# unused argument is their to force dependency hierarchy
# pylint: disable=unused-argument


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

    launchpad = environment.fixtures().get_plugin(
        interfaces=[METTA_PLUGIN_INTERFACE_ROLE_PROVISIONER],
        plugin_id=METTA_LAUNCHPAD_PROVISIONER_PLUGIN_ID,
    )

    terraform = environment.fixtures().get_plugin(
        interfaces=[METTA_PLUGIN_INTERFACE_ROLE_PROVISIONER],
        plugin_id=METTA_TERRAFORM_PROVISIONER_PLUGIN_ID,
    )

    # We will use this config to make decisions about what we need to create
    # and destroy for this environment up.
    conf = environment.config().load("config")
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
    conf = environment.config().load("config")
    """ somewhat equivalent to reading ./config/config.yml """

    launchpad = environment.fixtures().get_plugin(
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
    conf = environment.config().load("config")
    """ somewhat equivalent to reading ./config/config.yml """

    launchpad = environment.fixtures().get_plugin(
        interfaces=[METTA_PLUGIN_INTERFACE_ROLE_PROVISIONER],
        plugin_id=METTA_LAUNCHPAD_PROVISIONER_PLUGIN_ID,
    )

    terraform = environment.fixtures().get_plugin(
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


@pytest.fixture(scope="session", autouse=True)
def healthpoller_up(environment_before_up: Environment) -> HealthPollWorkload:
    """Start a running health poll and return it."""
    healthpoll_workload = environment_before_up.fixtures.get_plugin(
        plugin_id=METTA_PLUGIN_ID_WORKLOAD_HEALTHPOLL
    )

    healthpoll_workload.prepare(environment_before_up.fixtures)
    healthpoll_workload.apply()

    yield healthpoll_workload

    healthpoll_workload.destroy()


@pytest.fixture(scope="session")
def workloads(environment_up: Environment) -> Fixtures:
    """Returns a Fixtures set of workload plugins.

    These are the plugins that are meant to apply load
    to the cluster during the longevity test, and will
    not include the healthpolling workload.

    Returns:
    --------
    Fixtures list of workloads.

    """
    workload_fixtures = Fixtures()

    # Take any workload plugin other than the healthpoll plugin
    for fixture in environment_up.fixtures().filter(
        interfaces=[METTA_PLUGIN_INTERFACE_ROLE_WORKLOAD]
    ):
        if fixture.plugin_id == METTA_PLUGIN_ID_WORKLOAD_HEALTHPOLL:
            continue

        workload_fixtures.add(fixture)

    return workload_fixtures


@pytest.fixture(scope="module")
def workloads_up(environment_up: Environment, workloads: Fixtures) -> Fixtures:
    """Create and apply instances for all workloads."""
    for workload in workloads:
        plugin = workload.plugin
        if hasattr(plugin, "prepare"):
            plugin.prepare(environment_up.fixtures())
        if hasattr(plugin, "apply"):
            plugin.apply()
            logger.info("Workload %s applied.", workload.instance_id)
        else:
            logger.info("Workload %s created.", workload.instance_id)

    yield workloads

    for workload in workloads:
        plugin = workload.plugin
        if hasattr(plugin, "destroy"):
            plugin.destroy()
