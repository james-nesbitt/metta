"""

Run a healtcheck testing.

It makes sense to run this after all of the other tests.

The fixture used for this test is started in conftest.py before the first test
is run, and is constantly polling in the background.

"""

import logging

import pytest

from mirantis.testing.metta.healthcheck import HealthStatus


logger = logging.getLogger("test_clients.healthpoll")


@pytest.mark.last
def test_healthcheck_status(healthpoller):
    """Check the healthcheck poller."""
    health = healthpoller.health()
    poll_count = healthpoller.poll_count

    logger.info(
        "HealthCheck [%s polls completed] Status: %s",
        poll_count,
        health.status,
    )
    for message in health.messages:
        logger.info(message)

    # Assert that we have nothing more than a warning
    assert health.status.is_better_than(HealthStatus.ERROR)
