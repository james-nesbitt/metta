import logging
import json

from . import stability_test

logger = logging.getLogger('npods-test-longstability')
""" test-suite logger """

def test_01_target_stability(environment_up_unlocked, mke,
                            kubeapi, loki, npods, npods_config):
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

    logger.info(
        "stability test harness {} : {}+ (replicas) / {} + (threads)".format(
            name,
            workload['replicas'],
            workload['threads']))
    logger.debug(
        "Workloads: {}".format(
            json.dumps(
                npods.values["workloads"],
                indent=2)))

    try:
        npods.apply(wait=True)
    except Exception as e:
        logger.error("Helm could not scale up the npods workloads")
        raise RuntimeError(
            "Helm could not scale up the npods workloads") from e

    duration = int(
        npods_config.get(
            'tests.stability.duration'))
    """ how long to run the whole stability test """
    period = int(
        npods_config.get(
            'tests.stability.period'))
    """ how long to wait between each test iteration """

    try:
        stability_test(
            environment=environment_up_unlocked,
            mke=mke, kubeapi=kubeapi,
            npods_config=npods_config,
            logger=logger.getChild(name), duration=duration, period=period)
    except Exception as e:
        logger.error("Cluster stability test failed on scaled up cluster {}".format(name))
        raise RuntimeError(
            "Cluster stability test failed on scaled up cluster") from e

def test_02_scaledown_stability(environment_up_unlocked, mke,
                    kubeapi, loki, npods, npods_config):
    """ Scale down and test stability """

    name = "reset"

    # Reset to the original helm chart
    workload = npods.values["workloads"][0]
    npods.values["workloads"] = [workload]


    logger.info(
        "scaling down test harness to original spec: {} (replicas) / {} (threads)".format(
            name,
            workload['replicas'],
            workload['threads']))
    logger.debug(
        "Workloads: {}".format(
            json.dumps(
                npods.values["workloads"],
                indent=2)))

    try:
        npods.apply(wait=True)
    except Exception as e:
        logger.error("Helm could not scale down the npods workloads")
        raise RuntimeError(
            "Helm could not scale down the npods workloads") from e

    duration = int(
        npods_config.get(
            'tests.scale.duration'))
    """ how long to run the whole stability test """
    period = int(
        npods_config.get(
            'tests.scale.period'))
    """ how long to wait between each test iteration """

    try:
        stability_test(
            environment=environment_up_unlocked,
            mke=mke, kubeapi=kubeapi,
            npods_config=npods_config,
            logger=logger.getChild(name), duration=duration, period=period)
    except Exception as e:
        logger.error("Cluster stability test failed on scaled down cluster {}".format(name))
        raise RuntimeError(
            "Cluster stability test failed on scaled down cluster") from e
