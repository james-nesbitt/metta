"""

Run a workload stability test.

"""
import time
import logging

from mirantis.testing.metta.healthcheck import HealthStatus


logger = logging.getLogger("testkit-stability-test")


# pylint: disable=unused-argument
def test_01_workloads_up(workloads_up, healthpoller):
    """Ensure that the fixtures get created."""
    for i in range(1, 10):
        time.sleep(10)

        health = healthpoller.health()
        poll_count = healthpoller.poll_count()

        logger.info(
            "HealthCheck %s [%s polls completed] Status: %s",
            i,
            poll_count,
            health.status(),
        )
        for message in health.messages():
            logger.info(message)

        assert health.status().is_better_than(HealthStatus.ERROR), "Health was not good."
