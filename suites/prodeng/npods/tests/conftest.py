"""

PyTest NPods specific fixtures.

Fixtures that are common only to these npods tests, so they are kept out of the outer
conftest file.

"""
import logging
import json

import pytest

from mirantis.testing.metta_mirantis.mke_client import (
    METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID,
)
from mirantis.testing.metta_kubernetes import METTA_PLUGIN_ID_KUBERNETES_CLIENT

logger = logging.getLogger("npods-test-conftest")
""" test-suite logger """

# ------ FIXTURES ------------------------------------------

# impossible to chain pytest fixtures without using the same names
# pylint: disable=redefined-outer-name
# unused argument is their to force dependency hierarchy
# pylint: disable=unused-argument


@pytest.fixture(scope="package")
def npods_config(environment):
    """Get the npods yaml config object."""
    loaded = environment.config.load("npods")
    logger.info("Using npods config: %s", json.dumps(loaded.get(), indent=2))
    return loaded


@pytest.fixture(scope="package")
def mke(environment):
    """Get the mke client."""
    try:
        return environment.fixtures.get_plugin(
            plugin_id=METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID,
        )

    except KeyError as err:
        raise ValueError("No MKE client could be found. Is MKE installed?") from err


@pytest.fixture(scope="package")
def kubeapi(environment):
    """Get the kubeapi client and wait for it to be ready."""
    try:
        kubeapi_client = environment.fixtures.get_plugin(
            plugin_id=METTA_PLUGIN_ID_KUBERNETES_CLIENT,
        )

        try:
            # helms wil fail if the kubeapi isn't ready
            logger.info("Waiting for kubernetes to be ready")
            # general wait using readyz
            kubeapi_client.readyz_wait(45)
            # full wait until all kubelets are ready, or daemonsets will fail.
            kubeapi_client.kubelet_ready_wait(45)

        except Exception as err:
            raise Exception("Failed waiting for kubernetes to be ready") from err

        return kubeapi_client

    except KeyError as err:
        raise ValueError(
            "No Kubernetes client could be found. Is Kubernetes orchestration enabled??"
        ) from err


@pytest.fixture(scope="package")
def environment_up_unlocked(environment_up, mke, kubeapi):
    """Return environment with pods-per-node unlocked using the mke client.

    Use this to get the environment object, after the pods/node limit has
    been raised.

    This also performs an environment sanity test on clients.

    """
    try:
        data = mke.api_ucp_configtoml_get()
        data["cluster_config"]["kubelet_max_pods"] = 2000
        mke.api_ucp_configtoml_put(data)

    except Exception as err:
        raise Exception(
            "Failed when trying to raise the MKE limits for pods/node"
        ) from err

    # we didn't touch this but this is the return target
    return environment_up


@pytest.fixture(scope="module")
def healthpoller(environment_up):
    """Start the healthpoller."""
    healthpoller_plugin = environment_up.fixtures.get_plugin(instance_id="healthpoller")
    """ healthpoller workload defined in fixtures.yml, using fixtures from our environment """

    try:
        healthpoller_plugin.prepare(environment_up.fixtures)
        healthpoller_plugin.apply()
    except Exception as err:
        raise RuntimeError(
            "healthpoller_plugin failed to initialize before running test"
        ) from err

    yield healthpoller_plugin

    healthpoller_plugin.destroy()


@pytest.fixture(scope="module")
def npods(environment_up_unlocked, npods_config):
    """Create helm workload plugin using fixtures from our env."""
    npods_plugin = environment_up_unlocked.fixtures.get_plugin(
        instance_id="npods-workload"
    )
    """ npods helm workload defined in fixtures.yml, using fixtures from our environment """

    try:
        npods_plugin.prepare(environment_up_unlocked.fixtures)
        npods_plugin.apply(wait=True)
    except Exception as err:
        raise RuntimeError(
            "Npods helm stack failed to initialize before running test"
        ) from err

    yield npods_plugin

    npods_plugin.destroy()


@pytest.fixture(scope="package")
def loki(environment_up, npods_config):
    """Create monitoring helm workload plugin using fixtures from our env."""
    loki_plugin = environment_up.fixtures.get_plugin(instance_id="loki-workload")
    """ loki helm workload defined in fixtures.yml, using fixtures from our environment """

    try:
        logger.info("Starting loki monitoring stack")
        loki_plugin.prepare(environment_up.fixtures)
        loki_plugin.apply(wait=True)

    # pylint: disable=broad-except
    except BaseException:
        # this is not a blocking failure
        logger.error("Loki monitoring stack failed to start")

    return loki_plugin

    # we don't yield as typically you want this stack to stay in place after the run.
