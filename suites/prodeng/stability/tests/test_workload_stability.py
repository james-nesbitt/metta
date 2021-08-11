"""

Run a workload stability test.

"""
import logging
import time

from mirantis.testing.metta_health.healthcheck import HealthStatus


logger = logging.getLogger("stability-test")


# pylint: disable=unused-argument
def test_01_workloads_up(healthpoller, workloads_up):
    """Ensure that the fixtures are healthy after 1 minute."""

    time.sleep(60)

    poll_count = healthpoller.poll_count()
    health = healthpoller.health()
    messages = list(health.messages())

    logger.info(
        "HealthCheck %s [%s polls completed] Status: %s [from time %s] ::"
        "\n-----------------------------------------------"
        "\n%s"
        "\n-----------------------------------------------",
        1,
        poll_count,
        health.status(),
        0,
        "\n".join(f"-->{message}" for message in messages),
    )

    assert health.status().is_better_than(HealthStatus.ERROR), "Health was not good"
