"""

Run the CNCF Conformance test suite.

"""
import time
import logging
import pytest

from mirantis.testing.metta.client import METTA_PLUGIN_TYPE_CLIENT
from mirantis.testing.metta.workload import METTA_PLUGIN_TYPE_WORKLOAD

from mirantis.testing.metta_kubernetes.kubeapi_client import METTA_PLUGIN_ID_KUBERNETES_CLIENT
from mirantis.testing.metta_sonobuoy import METTA_PLUGIN_ID_SONOBUOY_WORKLOAD
from mirantis.testing.metta_sonobuoy.sonobuoy import Status

logger = logging.getLogger("cncf conformance")

SONOBUOY_TEST_INTERESTING_PLUGINS = ['e2e']
""" we only care about this plugin, the others can fail """
SONOBUOY_TEST_TIMER_LIMIT = 1440
""" time limit test run in second """
SONOBUOY_TEST_TIMER_STEP = 10
""" check status every X seconds """


# impossible to chain pytest fixtures without using the same names
# pylint: disable=redefined-outer-name


@pytest.fixture(scope="package")
def kubeapi_client(environment):
    """Get the kubeapi client plugin."""
    try:
        kubeapi_client = environment.fixtures.get_plugin(
            plugin_type=METTA_PLUGIN_TYPE_CLIENT, plugin_id=METTA_PLUGIN_ID_KUBERNETES_CLIENT)

        logger.info("Waiting for kubernetes to report readiness")
        kubeapi_client.readyz_wait(45)

        # Sometimes the sonobuoy pod gives an unavoidable taint error, even
        # though we are passing taint skips.  This is solved by a wait, so
        # it is likely a deeper k8 isn't ready issue (poor dignosis).
        logger.info("Forcing sleep to wait for kubernetes.")
        time.sleep(60)

        return kubeapi_client

    except KeyError as err:
        raise ValueError(
            "No Kubernetes client could be found. Is Kubernetes orchestration enabled??") from err


@pytest.fixture(scope="package")
def cncf_workload(environment_up):
    """Retrieve the CNCF workload instance."""
    return environment_up.fixtures.get_plugin(plugin_type=METTA_PLUGIN_TYPE_WORKLOAD,
                                              plugin_id=METTA_PLUGIN_ID_SONOBUOY_WORKLOAD)


@pytest.fixture()
def cncf_workload_instance(environment_up, cncf_workload):
    """Retrieve an individual worload instance from the cncf plugin."""
    return cncf_workload.create_instance(environment_up.fixtures)


def test_cncf_conformance(cncf_workload_instance, kubeapi_client):
    """Run cncf conformance test suite."""
    try:

        logger.info("Checking if kubernetes thinks it is ready")
        logger.debug("Kube readyz: %s", kubeapi_client.readyz())

        # start the CNCF conformance run
        logger.info("Starting sonobuoy run")
        cncf_workload_instance.apply(wait=True)
        logger.debug("Sonobuoy started, waiting for finish")

        # Every X seconds output some status report to show that it is still
        # working
        for i in range(0, round(SONOBUOY_TEST_TIMER_LIMIT /
                                SONOBUOY_TEST_TIMER_STEP)):
            status = cncf_workload_instance.status()

            if status is not None:
                for plugin_id in SONOBUOY_TEST_INTERESTING_PLUGINS:
                    if not status.plugin_status(plugin_id) in [
                            Status.COMPLETE, Status.FAILED]:
                        break

                    logger.debug("%s:: Checking %s:%s",
                                 i * SONOBUOY_TEST_TIMER_STEP, plugin_id,
                                 status.plugin(plugin_id))
                else:
                    break

            else:
                logger.debug("starting ...")

            logger.info("sonobuoy tick")
            time.sleep(SONOBUOY_TEST_TIMER_STEP)

        results = cncf_workload_instance.retrieve()

        no_errors = True
        for plugin_id in SONOBUOY_TEST_INTERESTING_PLUGINS:
            plugin_results = results.plugin(plugin_id)

            if plugin_results.status() in [Status.FAILED]:
                no_errors = False
                for item in plugin_results:
                    logger.error("%s: %s (%s)",
                                 plugin_id, item.name, item.meta_file_path())

        if not no_errors:
            raise RuntimeError("Sonobuoy encountered an error")

    finally:
        cncf_workload_instance.destroy(wait=True)
