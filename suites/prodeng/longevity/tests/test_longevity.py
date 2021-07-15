"""

Test that a cluster is stable for a long period of time.

Start some workloads on a cluster, and test stability over a long
period of time.

"""
import logging

from mirantis.testing.metta_common.healthpoll_workload import health_poller_output_log

logger = logging.getLogger("test-longevity")


# unused argument is their to force dependency hierarchy
# pylint: disable=unused-argument


def test_01_infra_up(environment_up):
    """Ensure that we have brought infrastructure up."""
    logger.info("Environment started successfully.")


def test_02_workloads_apply(workloads_up):
    """Ensure that we can apply workloads to the cluster."""
    logger.info("Cluster workloads applied and running.")


def test_03_longevity_wait(workloads_up, healthpoller):
    """Ensure that the fixtures get created and that they are health for 2 hours."""
    poll_logger = logger.getChild("healthpoller")
    """Use a new logger just for the health output."""

    # use a common function for logging poller status
    health_poller_output_log(
        healthpoller=healthpoller, poll_logger=poll_logger, period=30, count=4
    )
