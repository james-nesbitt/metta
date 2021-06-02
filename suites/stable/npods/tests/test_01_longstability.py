"""

Test 01 : Long stability test

Test that the MKE cluster remains stable with a steady number of pods for a long period of time.

"""
import logging
import json

from .checks import stability_test

logger = logging.getLogger('npods-test-longstability')
""" test-suite logger """


# pylint: disable=too-many-arguments, unused-argument
def test_01_target_stability(environment_up_unlocked, mke, kubeapi, loki, npods, npods_config):
    """ Long run of a fixed size stability test """
    # create a new workload
    workload = npods_config.get('workload.stability').copy()
    workload.update({
        'replicas': 1500,
        'threads': 1500
    })

    name = "npods-stability"
    workload['name'] = name

    # Add the workload to the helm chart
    npods.values["workloads"].append(workload)

    logger.info("stability test harness %s : %s+ (replicas) / %s + (threads)",
                name, workload['replicas'], workload['threads'])
    logger.debug("Workloads: %s", npods.values["workloads"])

    try:
        npods.apply(wait=True)
    except Exception as err:
        logger.error("Helm could not scale up the npods workloads")
        raise RuntimeError("Helm could not scale up the npods workloads") from err

    duration = int(npods_config.get('tests.stability.duration'))
    """ how long to run the whole stability test """
    period = int(npods_config.get('tests.stability.period'))
    """ how long to wait between each test iteration """

    try:
        stability_test(
            environment=environment_up_unlocked,
            mke=mke, kubeapi=kubeapi,
            npods_config=npods_config,
            logger=logger.getChild(name), duration=duration, period=period)
    except Exception as err:
        logger.error("Cluster stability test failed on scaled up cluster %s", name)
        raise RuntimeError("Cluster stability test failed on scaled up cluster") from err


def test_02_scaledown_stability(environment_up_unlocked, mke, kubeapi, loki, npods, npods_config):
    """ Scale down and test stability """

    name = "reset"

    # Reset to the original helm chart
    workload = npods.values["workloads"][0]
    npods.values["workloads"] = [workload]

    logger.info("scaling down %s test harness to original spec: %s (replicas) / %s (threads)",
                name, workload['replicas'], workload['threads'])
    logger.debug("Workloads: %s", json.dumps(npods.values["workloads"], indent=2))

    try:
        npods.apply(wait=True)
    except Exception as err:
        logger.error("Helm could not scale down the npods workloads")
        raise RuntimeError("Helm could not scale down the npods workloads") from err

    duration = int(npods_config.get('tests.scale.duration'))
    """ how long to run the whole stability test """
    period = int(npods_config.get('tests.scale.period'))
    """ how long to wait between each test iteration """

    try:
        stability_test(
            environment=environment_up_unlocked,
            mke=mke, kubeapi=kubeapi,
            npods_config=npods_config,
            logger=logger.getChild(name), duration=duration, period=period)
    except Exception as err:
        logger.error("Cluster stability test failed on scaled down cluster %s", name)
        raise RuntimeError("Cluster stability test failed on scaled down cluster") from err
