"""

Test that we can apply nPods per node.

This test case uses fixtures for environment control and test apparatus from
the local conftest.py.

The test case is a scaling test where increasing deployment/service workload is
added to the cluster until a high scale is reached.  Stability of the cluster is
tested between scaling operations for a set duration before moving to the next
scaling operation.

Health is tested via a set of health functions:
1. MKE Node health - ask the MKE api nodes endpoint if the nodes are healthy;
2. K8s pod health - ask the Kubernetes namespaced pods endpoint if the created
   pods are healthy.

PyTest test-function registration happend at the bottom, where we use an
abstraction to add test case functions as implmenetations of the
"scale and test" call.

"""
import logging
import json

from .checks import stability_test

logger = logging.getLogger("npods-test-scaling")
""" test-suite logger """


STABILITY_TEST_DURATION_DEFAULT = 5 * 60
""" default for how long we should run the test before we accept its stability (seconds) """
STABILITY_TEST_PERIOD_DEFAULT = 30
""" default for how frequently we should test stability (seconds) """

# ------ UTILITY -------------------------------------------


# pylint: disable=invalid-name
total = 0
""" track how many pods have we scaled up to """


def _create_scale_and_test_function(scale):
    """Create a function to scale to a certain number of pods and test stability.

    Parameters:
    -----------

    scale (Dict[str,Any]) : A Dict of workload values to use to override defaults
        in an operation to scale up the overall workload.

    Returns:

    a function which accepts only pytest fixtures that will scale and test the
    cluster stability.

    """

    # pylint: disable=too-many-arguments, unused-argument
    def _scale_and_test(healthpoller, loki, npods, npods_config):
        """Scale up the workloads and test stability."""

        # pylint: disable=global-statement
        global total

        # create a new workload
        workload = npods_config.get("workload.scale").copy()
        workload.update(scale)

        new_total = total + workload["replicas"]
        name = scale["name"] if "name" in scale else "{:04d}".format(new_total)
        workload["name"] = name

        # Add the workload to the helm chart
        npods.values["workloads"].append(workload)

        logger.info(
            "scaling test harness %s : %s+ (replicas) / %s+ (threads)",
            name,
            workload["replicas"],
            workload["threads"],
        )
        logger.debug("Workloads: %s", json.dumps(npods.values["workloads"], indent=2))

        try:
            npods.apply(wait=True)
        except Exception as err:
            logger.error("Helm could not scale up the npods workloads")
            raise RuntimeError("Helm could not scale up the npods workloads") from err

        # store the new total value after helm has been applied, and before we
        # test stability, in case the stability test throws an exception
        total = new_total

        duration = int(
            npods_config.get("tests.scale.duration", default=STABILITY_TEST_DURATION_DEFAULT)
        )
        """ how long to run the whole stability test """
        period = int(npods_config.get("tests.scale.period", default=STABILITY_TEST_PERIOD_DEFAULT))
        """ how long to wait between each test iteration """

        try:
            stability_test(
                healthpoller=healthpoller,
                logger=logger.getChild(name),
                duration=duration,
                period=period,
            )
        except Exception as err:
            logger.error("Cluster stability test failed on scaled up cluster %s", name)
            raise RuntimeError("Cluster stability test failed on scaled up cluster") from err

    return _scale_and_test


def _create_scale_down_and_test_function():
    """Create a function that will test scaling down the deployments"""

    # pylint: disable=too-many-arguments, unused-argument
    def scale_down_and_test(healthpoller, loki, npods, npods_config):
        """Scale down and test stability"""

        name = "reset"

        # Reset to the original helm chart
        workload = npods.values["workloads"][0]
        npods.values["workloads"] = [workload]

        logger.info(
            "scaling down %s test harness to original spec: %s (replicas) / %s (threads)",
            name,
            workload["replicas"],
            workload["threads"],
        )
        logger.debug("Workloads: %s", json.dumps(npods.values["workloads"], indent=2))

        try:
            npods.apply(wait=True)

        except Exception as err:
            logger.error("Helm could not scale down the npods workloads")
            raise RuntimeError("Helm could not scale down the npods workloads") from err

        duration = int(
            npods_config.get("tests.scale.duration", default=STABILITY_TEST_DURATION_DEFAULT)
        )
        """ how long to run the whole stability test """
        period = int(npods_config.get("tests.scale.period", default=STABILITY_TEST_PERIOD_DEFAULT))
        """ how long to wait between each test iteration """

        try:
            stability_test(
                healthpoller=healthpoller,
                logger=logger.getChild(name),
                duration=duration,
                period=period,
            )

        except Exception as err:
            logger.error("Cluster stability test failed on scaled down cluster %s", name)
            raise RuntimeError("Cluster stability test failed on scaled down cluster") from err

    return scale_down_and_test


# ------ TEST CASES ---------------------------------------


test_01_0500 = _create_scale_and_test_function({"replicas": 500, "threads": 500})
""" Initial scale up to 500 pods """
test_02_1000 = _create_scale_and_test_function({"replicas": 500, "threads": 500})
""" Scale up to 1000 pods """
test_03_1500 = _create_scale_and_test_function({"replicas": 500, "threads": 500})
""" Scale up to 1500 pods """
test_04_2000 = _create_scale_and_test_function({"replicas": 500, "threads": 500})
""" Scale up to 2000 pods """
test_05_2250 = _create_scale_and_test_function({"replicas": 250, "threads": 250})
""" Scale up to 2250 pods """
test_06_2500 = _create_scale_and_test_function({"replicas": 250, "threads": 250})
""" Scale up to 2500 pods """
test_05_2750 = _create_scale_and_test_function({"replicas": 250, "threads": 250})
""" Scale up to 2750 pods """
test_05_3000 = _create_scale_and_test_function({"replicas": 250, "threads": 250})
""" Scale up to 3000 pods """
test_06_down = _create_scale_down_and_test_function()
""" Scale back down test """
