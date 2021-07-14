"""

Test that a cluster is stable for a long period of time.

Start some workloads on a cluster, and test stability over a long
period of time.

"""
import logging
import time

from mirantis.testing.metta.healthcheck import HealthStatus


logger = logging.getLogger("test-longevity")


# unused argument is their to force dependency hierarchy
# pylint: disable=unused-argument


def test_01_infra_up(environment_up):
    """Ensure that we have brought infrastructure up."""
    logger.info("Environment started successfully.")


def test_02_workloads_apply(workloads_up):
    """Ensure that we can apply workloads to the cluster."""
    logger.info("Cluster workloads applied and running.")


def test_03_longevity_wait(healthpoller):
    """Start the longevity stability poll."""
    logger.info("Starting longevity monitoring of health polling.")
    for i in range(0, 40):
        time.sleep(1800)

        health = healthpoller.health()
        poll_count = healthpoller.poll_count()

        logger.info(
            "HealthCheck %s [%s polls completed] Status: %s",
            i,
            poll_count,
            health.status,
        )
        for message in health.messages:
            logger.info(message)

        assert health.status.is_better_than(HealthStatus.ERROR), "Health was not good."
