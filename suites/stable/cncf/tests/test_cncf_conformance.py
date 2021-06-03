"""

Test that some clients work

"""
import time
import logging
import pytest

from mirantis.testing.metta.workload import METTA_PLUGIN_TYPE_WORKLOAD

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


@pytest.fixture(scope="module")
def cncf_workload(environment_up):
    """Retrieve the CNCF workload instance."""

    # if we don't put in a small delay then we get an error out of sonobuoy:
    # e2e: Can't schedule pod: 0/1 nodes are available: 1 node(s) had taint \
    #      {com.docker.ucp.manager: }, that the pod didn't tolerate. \
    #      (errors/global/error.json)
    #
    # This error goes away with a short delay.

    return environment_up.fixtures.get_plugin(plugin_type=METTA_PLUGIN_TYPE_WORKLOAD,
                                              plugin_id=METTA_PLUGIN_ID_SONOBUOY_WORKLOAD,
                                              instance_id='cncf')


@pytest.fixture()
def cncf_workload_instance(environment_up, cncf_workload):
    """Retrieve an individual worload instance from the cncf plugin."""
    return cncf_workload.create_instance(environment_up.fixtures)


def test_cncf_conformance(cncf_workload_instance):
    """ run cncf conformance test suite """
    try:
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
