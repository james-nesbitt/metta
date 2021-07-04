"""Some common fixtures"""
import logging

import pytest

from mirantis.testing.metta_kubernetes import METTA_PLUGIN_ID_KUBERNETES_CLIENT


logger = logging.getLogger("test_clients.fixtures")

DEFAULT_K8S_NAMESPACE = "default"


@pytest.fixture(scope="session", autouse=True)
def healthpoller(environment_up):
    """Get the healtcheck polling workload from fixtures/yml."""
    workload_plugin = environment_up.fixtures.get_plugin(instance_id="healthpoll")
    logger.info("Starting background health poll workload.")

    workload_plugin.prepare(environment_up.fixtures)
    workload_plugin.apply()

    yield workload_plugin

    workload_plugin.destroy()


@pytest.fixture(scope="session")
def kubeapi_client(environment_up):
    """Retrieve a kubeapi client for comparitive testing."""
    return environment_up.fixtures.get_plugin(
        plugin_id=METTA_PLUGIN_ID_KUBERNETES_CLIENT,
    )
