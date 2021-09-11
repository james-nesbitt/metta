"""

Run the Sonobuoy AzureArc validation test suite.

"""
import logging

import pytest

from mirantis.testing.metta_sonobuoy.workload import (
    METTA_SONOBUOY_WORKLOAD_PLUGIN_ID,
    SonobuoyWorkloadPlugin,
)

from mirantis.testing.metta_sonobuoy.results import Status

logger = logging.getLogger("cncf conformance")

SONOBUOY_TEST_TIMER_LIMIT = 7200
""" time limit test run in seconds """
SONOBUOY_TEST_TIMER_STEP = 60
""" check status every X seconds """

ENVIRONMENT_STATE = "345-138"

# impossible to chain pytest fixtures without using the same names
# pylint: disable=redefined-outer-name
# unused argument is their to force dependency hierarchy
# pylint: disable=unused-argument


@pytest.fixture(scope="module")
def sonobuoy_workload(environment_up, kubeapi_client) -> SonobuoyWorkloadPlugin:
    """Retrieve the azurearc workload instance."""
    # Make sure that we are in the desired state
    environment_up.set_state(ENVIRONMENT_STATE)
    # Get the sonobuoy plugin
    plugin: SonobuoyWorkloadPlugin = environment_up.fixtures().get_plugin(
        interfaces=[METTA_SONOBUOY_WORKLOAD_PLUGIN_ID]
    )

    # start the CNCF conformance run
    logger.info("Starting sonobuoy run")
    plugin.prepare(environment_up.fixtures())

    yield plugin

    plugin.destroy()


def test_start_sonobuoy(sonobuoy_workload):
    """Start sonobuoy test suite."""
    logger.debug("Sonobuoy starting, waiting for finish")
    sonobuoy_workload.apply(wait=True)


def test_retrieve_cncf_conformance(sonobuoy_workload):
    """Retrieve azurearc conformance test suite results."""
    results = sonobuoy_workload.retrieve()

    status = sonobuoy_workload.status()
    has_errors = False
    for plugin_id in status.plugin_list():
        plugin_results = results.plugin(plugin_id)

        if plugin_results.status() in [Status.FAILED]:
            logger.error("Sonobuoy result is marked as failed: %s", plugin_results.status())
            has_errors = True
            for item in plugin_results:
                logger.error("%s: %s (%s)", plugin_id, item.name, item.meta_file_path())

    if not has_errors:
        raise RuntimeError("Sonobuoy encountered an error")
