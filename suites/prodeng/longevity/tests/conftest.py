"""

Fixtures and pytest overloads for the longevity test.

These fixtures fast track and isolate plugin isolation
form test functions, and may tweak reporting.

"""

import logging
import pytest

from mirantis.testing.metta.fixture import Fixtures
from mirantis.testing.metta.workload import METTA_PLUGIN_INTERFACE_ROLE_WORKLOAD

from mirantis.testing.metta_health.healthpoll_workload import (
    METTA_PLUGIN_ID_WORKLOAD_HEALTHPOLL,
    HealthPollWorkload,
)

logger = logging.getLogger("longevity-conftest")

# impossible to chain pytest fixtures without using the same names
# pylint: disable=redefined-outer-name
# unused argument is their to force dependency hierarchy
# pylint: disable=unused-argument


@pytest.fixture(scope="session")
def workloads(environment_up) -> Fixtures:
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
def workloads_up(environment_up, workloads) -> Fixtures:
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


@pytest.fixture(scope="module")
def healthpoller(environment_up) -> HealthPollWorkload:
    """Start a running health poll and return it."""
    healthpoll_workload = environment_up.fixtures().get_plugin(
        plugin_id=METTA_PLUGIN_ID_WORKLOAD_HEALTHPOLL
    )

    healthpoll_workload.prepare(environment_up.fixtures())
    healthpoll_workload.apply()

    yield healthpoll_workload

    healthpoll_workload.destroy()
