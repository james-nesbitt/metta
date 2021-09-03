"""

Run a workload upgrade test.

"""
import logging
import time

from mirantis.testing.metta_health.healthcheck import HealthStatus


logger = logging.getLogger("upgrade-test")

# pylint: disable=unused-argument


def test_01_install(environment):
    """Run the initial install by activating the state."""
    logger.info("Activating install environment.")
    environment.set_state("install")


def test_02_post_install(environment):
    """Run initial workloads by activating the post-install state."""
    logger.info("Activating post-install environment.")
    environment.set_state("post-install")


def test_03_upgrade1(environment):
    """Run an upgrade install by activating the first state."""
    logger.info("Activating upgrade1 environment.")
    environment.set_state("upgrade1")


def test_04_upgrade2(environment):
    """Run an upgrade install by activating the second upgrade state."""
    logger.info("Activating upgrade2 environment.")
    environment.set_state("upgrade2")


def test_10_healthcheck(environment, healthpoller):
    """Ensure that the fixtures are healthy after 10 minutes."""
    logger.info("Activating post-upgrade environment.")
    environment.set_state("post-upgrade")

    time.sleep(10 * 60)

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
