"""

Run the CNCF Conformance test suite.

"""
import logging

import pytest

from mirantis.testing.metta_health.healthpoll_workload import (
    HealthPollWorkload,
    METTA_PLUGIN_ID_WORKLOAD_HEALTHPOLL,
)
from mirantis.testing.metta_kubernetes.kubeapi_client import (
    METTA_PLUGIN_ID_KUBERNETES_CLIENT,
    KubernetesApiClientPlugin,
)

logger = logging.getLogger("azurearc-fixtures")

SONOBUOY_TEST_TIMER_LIMIT = 1440
""" time limit test run in second """
SONOBUOY_TEST_TIMER_STEP = 10
""" check status every X seconds """


# impossible to chain pytest fixtures without using the same names
# pylint: disable=redefined-outer-name
# unused argument is their to force dependency hierarchy
# pylint: disable=unused-argument


@pytest.fixture(scope="package")
def kubeapi_client(environment) -> KubernetesApiClientPlugin:
    """Get the kubeapi client plugin but wait for k8s to be ready."""
    try:
        kubeapi_client: KubernetesApiClientPlugin = environment.fixtures().get_plugin(
            interfaces=[METTA_PLUGIN_ID_KUBERNETES_CLIENT]
        )

    except KeyError as err:
        raise ValueError(
            "No Kubernetes client could be found. Is Kubernetes orchestration enabled??"
        ) from err

    logger.info("Waiting for kubernetes to report readiness")
    kubeapi_client.readyz_wait(45)
    kubeapi_client.kubelet_ready_wait(45)
    logger.info("Kubernetes thinks it is ready.")

    return kubeapi_client


@pytest.fixture(scope="module")
def healthpoller_up(environment_up) -> HealthPollWorkload:
    """Start a running health poll and return it."""
    healthpoll_workload = environment_up.fixtures().get_plugin(
        plugin_id=METTA_PLUGIN_ID_WORKLOAD_HEALTHPOLL
    )

    healthpoll_workload.prepare(environment_up.fixtures())
    healthpoll_workload.apply()

    yield healthpoll_workload

    healthpoll_workload.destroy()
