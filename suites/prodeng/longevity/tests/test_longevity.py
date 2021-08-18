"""

Test that a cluster is stable for a long period of time.

Start some workloads on a cluster, and test stability over a long
period of time.

"""
import logging
import time

from mirantis.testing.metta_health.healthcheck import HealthStatus

logger = logging.getLogger("test-longevity")


# unused argument is their to force dependency hierarchy
# pylint: disable=unused-argument


def test_01_infra_up(environment_up):
    """Ensure that we have brought infrastructure up."""
    logger.info("Environment started successfully.")


def test_02_workloads_apply(workloads_up):
    """Ensure that we can apply workloads to the cluster."""
    logger.info("Cluster workloads applied and running.")


def test_03_longevity_wait(environment, workloads_up, healthpoller):
    """Ensure that the fixtures get created and that they are health for 2 hours."""
    longevity_config = environment.config().load("longevity")
    """Load the longevity(.yml) configuration to get test conf."""

    count = int(longevity_config.get("count", default=10))
    """How many times should we ask healthpoller for a health update."""
    period = int(longevity_config.get("period", default=30))
    """How long should we wait between healthpoller requests."""

    # Periodically log a healthpoller plugins health results and logs.
    last_message_time = 0
    poll_logger = logger.getChild("healthpoller")
    """Use a new logger just for the health output."""
    for i in range(0, count):
        time.sleep(period)

        poll_count = healthpoller.poll_count()
        health = healthpoller.health()
        messages = list(health.messages(since=last_message_time))

        poll_logger.info(
            "HealthCheck %s [%s polls completed] Status: %s [from time %s] ::\n%s",
            i,
            poll_count,
            health.status(),
            int(last_message_time),
            "\n".join(f"-->{message}" for message in messages),
        )
        if len(messages) > 0:
            last_message_time = messages[-1].time

        assert health.status().is_better_than(HealthStatus.ERROR), "Health was not good"
