"""

Test that some clients work

"""

import logging
import time

import pytest

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.fixture import Fixtures
from mirantis.testing.metta_health.healthcheck import HealthStatus
from mirantis.testing.metta_health.healthpoll_workload import HealthPollWorkload
from mirantis.testing.metta_kubernetes.deployment_workload import (
    METTA_PLUGIN_ID_KUBERNETES_DEPLOYMENT_WORKLOAD,
    KubernetesDeploymentWorkloadPlugin,
)

logger = logging.getLogger("test_upgrade")


# pylint: disable=unused-argument
@pytest.mark.order(1)
def test_before_up(environment_before_up: Environment):
    """confirm that phase 1 has started"""
    logger.info("BEFORE: environment is confirmed up.")


@pytest.mark.order(1)
def test_kubernetes_deployment_workload(
    workloads_up: Fixtures,
):
    """test that we can get a k8s workload to run"""
    logger.info("Testing that the deployment workload is running.")

    stability_workload_up: KubernetesDeploymentWorkloadPlugin = workloads_up.get_plugin(
        plugin_id=METTA_PLUGIN_ID_KUBERNETES_DEPLOYMENT_WORKLOAD
    )
    deployment = stability_workload_up.read()

    assert deployment is not None
    logger.info("BEFORE: sanity workload deployed: %s}", deployment)

    metadata = deployment.metadata
    assert stability_workload_up.name == metadata.name
    assert stability_workload_up.namespace == metadata.namespace


# pylint: disable=unused-argument
@pytest.mark.order(2)
def test_after_up(environment_after_up: Environment):
    """confirm that phase 2 has started"""
    logger.info("AFTER: environment is confirmed up.")


@pytest.mark.order(2)
def test_kube_workload_still_running(
    environment_after_up: Environment,
    workloads: Fixtures,
):
    """did we get a good kubectl client"""
    logger.info("AFTER: Getting K8s test deployment which was run in the 'before' environment.")

    stability_workload_up: KubernetesDeploymentWorkloadPlugin = workloads.get_plugin(
        plugin_id=METTA_PLUGIN_ID_KUBERNETES_DEPLOYMENT_WORKLOAD
    )
    deployment = stability_workload_up.read()

    namespace = stability_workload_up.namespace
    name = stability_workload_up.name

    # The start test should have created this workload, so we should be able
    # to find it.
    assert deployment is not None, "Did not find the expected sanity workload running"
    logger.info(deployment)

    status = deployment.status
    assert status is not None
    logger.info("Sanity deployment status: %s", status)
    metadata = deployment.metadata
    assert name == metadata.name
    assert namespace == metadata.namespace

    # tear the deployment down
    status = stability_workload_up.destroy()
    assert status is not None
    assert status.code is None
    logger.info("Sanity deployment destroy status: %s", status)


@pytest.mark.order(2)
def test_healthpoller_check(
    environment_after_up: Environment, healthpoller_up: HealthPollWorkload
):
    """Ensure that the fixtures get created and that they are health for 2 hours."""
    count = 10
    """How many times should we ask healthpoller for a health update."""
    period = 30
    """How long should we wait between healthpoller requests."""

    # Periodically log a healthpoller plugins health results and logs.
    last_message_time = 0
    poll_logger = logger.getChild("healthpoller")
    """Use a new logger just for the health output."""
    for i in range(0, count):
        time.sleep(period)

        poll_count = healthpoller_up.poll_count()
        health = healthpoller_up.health()
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
