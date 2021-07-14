"""

Run the CNCF Conformance test suite.

"""
import time
import logging
from subprocess import CalledProcessError

from mirantis.testing.metta_sonobuoy.sonobuoy import Status

logger = logging.getLogger("cncf conformance")

SONOBUOY_TEST_TIMER_LIMIT = 7200
""" time limit test run in seconds """
SONOBUOY_TEST_TIMER_STEP = 60
""" check status every X seconds """


def test_start_cncf_conformance(cncf_workload):
    """Start cncf conformance test suite."""
    logger.debug("Sonobuoy started, waiting for finish")

    # Every X seconds output some status report to show that it is still
    # working
    for i in range(0, round(SONOBUOY_TEST_TIMER_LIMIT / SONOBUOY_TEST_TIMER_STEP)):
        # give one sleep just to give sonobuoy a change to start
        time.sleep(SONOBUOY_TEST_TIMER_STEP)

        try:
            status = cncf_workload.status()
        except CalledProcessError:
            status = None

        if status is not None:
            break

        logger.warning("Still starting sonobuoy (%s) ... %s", i, status)


def test_wait_cncf_conformance(cncf_workload):
    """Wait for cncf conformance test suite to finish running."""
    # Every X seconds output some status report to show that it is still
    # working
    logger.info("Starting cncf plugin status poll to wait until work is finihsed.")

    start = time.perf_counter()
    """time when we starting tracking cncf progress."""

    now = 0
    while now < SONOBUOY_TEST_TIMER_LIMIT:
        time.sleep(SONOBUOY_TEST_TIMER_STEP)
        now = time.perf_counter() - start

        try:
            status = cncf_workload.status()
        except CalledProcessError:
            status = None

        if status is not None:
            still_running_count = 0
            for plugin_id in status.plugin_list():
                logger.info(
                    "%s:: Checking %s:%s", int(now), plugin_id, status.plugin(plugin_id)
                )

                if status.plugin_status(plugin_id) not in [
                    Status.COMPLETE,
                    Status.FAILED,
                ]:
                    still_running_count += 1

            if still_running_count == 0:
                logger.info(
                    "All plugins are marked completed or failed. Ending status poll."
                )
                break

        else:
            logger.warning("Could not retrieve status ...")

    status = cncf_workload.status()
    for plugin_id in status.plugin_list():
        logger.info(
            "%s:: Final status %s:%s",
            int(time.perf_counter()-start),
            plugin_id,
            status.plugin(plugin_id),
        )


def test_retrieve_cncf_conformance(cncf_workload):
    """Retrieve cncf conformance test suite results."""
    results = cncf_workload.retrieve()

    status = cncf_workload.status()
    no_errors = True
    for plugin_id in status.plugin_list():
        plugin_results = results.plugin(plugin_id)

        if plugin_results.status() in [Status.FAILED]:
            logger.error("Sonobuoy result is marked as failed: %s", plugin_results.status())
            no_errors = False
            for item in plugin_results:
                logger.error("%s: %s (%s)", plugin_id, item.name, item.meta_file_path())

    if not no_errors:
        raise RuntimeError("Sonobuoy encountered an error")
