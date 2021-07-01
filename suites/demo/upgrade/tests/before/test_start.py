"""

Test that some clients work

"""

import logging

import pytest

from mirantis.testing.metta.environment import Environment

from mirantis.testing.metta_kubernetes.deployment_workload import (
    KubernetesDeploymentWorkloadInstance,
)

logger = logging.getLogger("test_start")


# pylint: disable=unused-argument
@pytest.mark.order(1)
def test_before_up(environment_before_up: Environment):
    """confirm that phase 1 has started"""
    logger.info("BEFORE: environment is confirmed up.")


@pytest.mark.order(1)
def test_kubernetes_deployment_workload(
    stability_workload_instance: KubernetesDeploymentWorkloadInstance,
):
    """test that we can get a k8s workload to run"""
    logger.info(
        "Starting a kubernetes workload in this environment, so that we can "
        "confirm it is running after an upgrade."
    )

    deployment = stability_workload_instance.apply()
    assert deployment is not None
    logger.info("BEFORE: sanity workload deployed: %s}", deployment)

    metadata = deployment.metadata
    assert stability_workload_instance.name == metadata.name
    assert stability_workload_instance.namespace == metadata.namespace
