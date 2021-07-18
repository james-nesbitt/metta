"""

Run a workload stability test.

"""
import logging

from mirantis.testing.metta_common.healthpoll_workload import health_poller_output_log


logger = logging.getLogger("stability-test")


# pylint: disable=unused-argument
def test_01_workloads_up(healthpoller, nginx_deployment, metrics_deployment):
    """Ensure that the fixtures get created and that they are health for 2 minutes."""
    poll_logger = logger.getChild("healthpoller")
    """Use a new logger just for the health output."""

    # use a common function for logging poller status
    health_poller_output_log(healthpoller=healthpoller, poll_logger=poll_logger, period=30, count=4)
