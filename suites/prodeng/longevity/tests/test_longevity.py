"""

Test that a cluster is stable for a long period of time.

Start some workloads on a cluster, and test stability over a long
period of time.

"""
import logging
import time

from mirantis.testing.metta.healthcheck import Health


logger = logging.getLogger("test-longevity")


def test_01_infra_up(environment_up):
    """Ensure that we have brought infrastructure up."""
    logger.info("Environment started successfully.")


def test_02_workloads_apply(workload_instances_up):
    """Ensure that we can apply workloads to the cluster."""
    logger.info("Cluster workloads applied and running.")


def test_03_longevity_wait(healthpoll_instance):
    """Start the longevity stability poll."""
    for i in range(0, 4):
        time.sleep(1800)

        health = healthpoll_instance.health_aggregate()
        poll_count = healthpoll_instance.poll_count

        logger.info(
            "HealthCheck %s [%s polls completed] Status: %s",
            i,
            poll_count,
            health.status,
        )
        for message in health.messages:
            logger.info(message)


def _health_output(health: Health):
    """Log the health status."""
    logger.info("Status: %s", health.status)
    for message in health.messages:
        logger.info(message)
