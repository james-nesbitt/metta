"""

NPods health detection.

Various functions used to determine if a cluster is healthy.

"""
import logging
import time

from mirantis.testing.metta.healthcheck import HealthStatus

logger = logging.getLogger("npods-test")
""" test-suite logger """

# It is convenient to use the same name to allow a default fallback.
# pylint: disable=redefined-outer-name


# pylint: disable=too-many-arguments,unused-argument
def stability_test(healthpoller, logger, period, duration):
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
    start = time.time()
    timeout = start + duration

    index = 1
    logger.info(
        "Stability tests: Following health-check polling [period:%s/duration:%s]",
        period,
        duration,
    )
    # wait for the first period, to allow a system to stabilize before testing
    time.sleep(period)
    while time.time() < timeout:
        cycle_start = time.time()
        elapsed = int(cycle_start - start)

        health = healthpoller.health()
        poll_count = healthpoller.poll_count()

        logger.info(
            "HealthCheck %s [%s elapsed][%s polls completed] Status: %s",
            index,
            elapsed,
            poll_count,
            health.status,
        )
        for message in health.messages:
            logger.info(message)

        assert health.status.is_better_than(HealthStatus.ERROR), "Health was not good."

        cycle_elapsed = int(time.time() - cycle_start)
        cycle_remaining = int(period - cycle_elapsed) if period > cycle_elapsed else 0

        time.sleep(cycle_remaining)
        index += 1
