"""

NPods health detection.

Various functions used to determine if a cluster is healthy.

"""
import logging

from mirantis.testing.metta_common.healthpoll_workload import health_poller_output_log

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
    logger.info(
        "Stability tests: Following health-check polling [period:%s/duration:%s]",
        period,
        duration,
    )

    poll_logger = logger.getChild("healthpoller")
    """Use a new logger just for the health output."""

    # use a common function for logging poller status
    health_poller_output_log(
        healthpoller=healthpoller,
        poll_logger=poll_logger,
        period=period,
        count=int(duration / period),
    )
