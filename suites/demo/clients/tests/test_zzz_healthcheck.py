"""

Run a healtcheck testing.

It makes sense to run this after all of the other tests.

The fixture used for this test is started in conftest.py before the first test
is run, and is constantly polling in the background.

"""

import logging
import time

import pytest

from mirantis.testing.metta_health.healthcheck import HealthStatus


logger = logging.getLogger("test_clients.healthpoll")


def test_healthcheck_status(healthpoller):
    """Check the healthcheck poller."""
    time.sleep(30)

    health = healthpoller.health()
    logger.info(
        "HealthCheck %s [%s polls completed] Status: %s [from time %s] ::"
        "\n-----------------------------------------------"
        "\n%s"
        "\n-----------------------------------------------",
        1,
        healthpoller.poll_count(),
        health.status(),
        0,
        "\n".join(f"-->{message}" for message in list(health.messages())),
    )

    assert health.status().is_better_than(HealthStatus.ERROR), "Health was not good"

    # Assert that we have nothing more than a warning
    assert health.status().is_better_than(HealthStatus.ERROR)
