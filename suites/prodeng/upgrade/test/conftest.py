"""

PyTest fixtures for the upgrade test.

"""
import logging

import pytest

from mirantis.testing.metta_health.healthpoll_workload import (
    HealthPollWorkload,
    METTA_PLUGIN_ID_WORKLOAD_HEALTHPOLL,
)

logger = logging.getLogger("stability-conftest")

# impossible to chain pytest fixtures without using the same names
# pylint: disable=redefined-outer-name
# unused argument is their to force dependency hierarchy
# pylint: disable=unused-argument


@pytest.fixture(scope="module")
def healthpoller(environment) -> HealthPollWorkload:
    """Start a running health poll and return it."""
    healthpoll_workload = environment.fixtures().get_plugin(
        plugin_id=METTA_PLUGIN_ID_WORKLOAD_HEALTHPOLL
    )

    healthpoll_workload.prepare(environment.fixtures())
    healthpoll_workload.apply()

    yield healthpoll_workload

    healthpoll_workload.destroy()
