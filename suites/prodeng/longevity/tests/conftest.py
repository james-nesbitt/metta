"""

Fixtures and pytest overloads for the longevity test.

These fixtures fast track and isolate plugin isolation
form test functions, and may tweak reporting.

"""

import logging
import pytest

from mirantis.testing.metta.fixtures import Fixtures
from mirantis.testing.metta.workload import METTA_PLUGIN_TYPE_WORKLOAD

from mirantis.testing.metta_common.healthpoll_workload import (
    HealthPollWorkload,
    METTA_PLUGIN_ID_WORKLOAD_HEALTHPOLL,
)


logger = logging.getLogger("longevity-conftest")


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
    workloads = Fixtures()

    # Take any workload plugin other than the healthpoll plugin
    for fixture in environment_up.fixtures.filter(
        plugin_type=METTA_PLUGIN_TYPE_WORKLOAD
    ):
        if fixture.plugin_id != METTA_PLUGIN_ID_WORKLOAD_HEALTHPOLL:
            workloads.add(fixture)
    return workloads


@pytest.fixture(scope="module")
def workload_instances_up(environment_up, workloads):
    """Create and apply instances for all workloads."""
    instances = []
    for workload in workloads:
        instance = workload.plugin.create_instance(environment_up.fixtures)
        if hasattr(instance, "apply"):
            instance.apply()
            logger.info("Workload %s applied.", workload.instance_id)
        else:
            logger.info("Workload %s created.", workload.instance_id)
        instances.append(instance)

    yield instances

    for instance in instances:
        if hasattr(instance, "destroy"):
            instance.destroy()


@pytest.fixture(scope="module")
def healthpoll(environment_up) -> HealthPollWorkload:
    """Retrieve the health-poll workload plugin."""
    return environment_up.fixtures.get_plugin(
        plugin_id=METTA_PLUGIN_ID_WORKLOAD_HEALTHPOLL
    )


@pytest.fixture(scope="module")
def healthpoll_instance(environment_up, healthpoll):
    """Start a running health poll."""
    instance = healthpoll.create_instance(environment_up.fixtures)

    yield instance

    instance.stop()
