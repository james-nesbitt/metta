"""

NPods health detection.

Various functions used to determine if a cluster is healthy.

"""
from typing import Dict, List
import logging

from mirantis.testing.metta_health.healthpoll_workload import HealthPollWorkload
from mirantis.testing.metta_health.healthcheck import Health, HealthStatus, HealthException

logger = logging.getLogger("npods-test")
""" test-suite logger """

# It is convenient to use the same name to allow a default fallback.
# pylint: disable=redefined-outer-name


# pylint: disable=too-many-arguments,unused-argument
def stability_test(
    healthpoller: HealthPollWorkload,
    logger: logging.Logger,
    required_status: HealthStatus = HealthStatus.ERROR,
):
    """Run a stability test on the cluster.

    Parameters:
    -----------
    Healthtest polling workload, but also a logger.

    Returns:
    --------
    Nothing

    Raise:
    ------
    Raises an exception if more than 1 node is unhealthy

    """
    logger.info("Stability tests: Retrieving health-check polling")

    health_by_source: Dict[str, Health] = healthpoller.health_by_source()
    """Get a Health status from all sources."""

    errors: List[Exception] = []
    """Did any errors get returned during the health check."""

    for source, health in health_by_source.items():

        if health.status().is_better_than(HealthStatus.WARNING):
            logger.info("%s is Healthy", source)
        elif health.status().is_better_than(HealthStatus.ERROR):
            messages = (
                message
                for message in health.messages()
                if not message.status.is_better_than(HealthStatus.WARNING)
            )
            output = "\n".join(
                list(
                    f"{message.status}: {message.time} => {message.message}"
                    for message in messages
                )
            )
            logger.warning("%s has health warnings: %s", source, output)
        else:
            messages = (
                message
                for message in health.messages()
                if not message.status.is_better_than(HealthStatus.WARNING)
            )
            output = "\n".join(
                list(
                    f"{message.status}: {message.time} => {message.message}"
                    for message in messages
                )
            )
            logger.error("[%s] has health errors: %s", source, output)

        if required_status is None or health.status().is_better_than(required_status):
            continue

        errors.append(HealthException())
