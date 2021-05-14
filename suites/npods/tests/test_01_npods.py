"""

Test that we can apply nPods per node.

"""
import logging
import time
import json

from mirantis.testing.metta_mirantis.mke_client import MKENodeState

logger = logging.getLogger('npods-test')
""" test-suite logger """

STABILITY_TEST_DURATION_DEFAULT = 5 * 60
""" default for how long we should run the test before we accept its stability (seconds) """
STABILITY_TEST_PERIOD_DEFAULT = 30
""" default for how frequently we should test stability (seconds) """

# ------ UTILITY -------------------------------------------

total = 0
""" track how many pods have we scaled up to """


def _create_scale_and_test_function(scale):
    """ create a function to scale to a certain number of pods and test stability

    Parameters:
    -----------

    scale (Dict[str,Any]) : A Dict of workload values to use to override defaults
        in an operation to scale up the overall workload.

    Returns:

    a function which accepts only pytest fixtures that will scale and test the
    cluster stability.

    """

    def _scale_and_test(environment_up_unlocked, mke,
                        kubeapi, loki, npods, npods_config):
        """ Scale up the workloads and test stability """
        global total

        # create a new workload
        workload = npods_config.get('workload.default').copy()
        workload.update(scale)

        new_total = total + workload['replicas']
        name = scale['name'] if 'name' in scale else "{}".format(new_total)
        workload['name'] = name

        # Add the workload to the helm chart
        npods.values["workloads"].append(workload)

        logger.info(
            "scaling test harness {} : {}+ (replicas) / {} + (threads)".format(
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

        # store the new total value after helm has been applied, and before we
        # test stability, in case the stability test throws an exception
        total = new_total

        # stability test communicates by raising exceptions
        logger.info("Running stability test on scaled cluster")
        try:
            stability_test(
                environment=environment_up_unlocked,
                mke=mke, kubeapi=kubeapi,
                npods_config=npods_config,
                logger=logger.getChild(name))
        except Exception as e:
            logger.error("Cluster stability test failed on scaled up cluster")
            raise RuntimeError(
                "Cluster stability test failed on scaled up cluster") from e

    return _scale_and_test


def stability_test(environment, mke, kubeapi, npods_config, logger):
    """ Run a stability test on the cluster

    Parameters:
    -----------

    Mainly pytest fixtures, but also a logger.

    Returns:
    --------

    Nothing

    Raise:
    ------

    Raises an exception if more than 1 node is unhealthy

    """

    duration = int(
        npods_config.get(
            'stability_test.duration',
            default=STABILITY_TEST_DURATION_DEFAULT))
    start = time.time()
    timeout = start + duration
    """ how long to run the whole stability test """
    period = int(
        npods_config.get(
            'stability_test.period',
            default=STABILITY_TEST_PERIOD_DEFAULT))
    """ how long to wait between each test iteration """

    index = 1
    logger.info("Stability tests: starting health-check")
    while time.time() < timeout:
        cycle_start = time.time()
        elapsed = int(cycle_start - start)

        logger.info("Cycle  [{}] {} starting".format(index, elapsed))

        # for event in watch.stream(coreV1Api.list_namespaced_pod, namespace='npods', timeout_seconds=period):
        #     logger.info("Event: %s %s" % (event['type'], event['object'].metadata.name))

        mke_health(mke, logger)
        k8s_health(kubeapi, logger)

        cycle_elapsed = int(time.time() - cycle_start)
        cycle_remaining = int(
            period - cycle_elapsed) if period > cycle_elapsed else 0

        time.sleep(cycle_remaining)
        index += 1


def mke_health(mke, logger):
    """ Does MKE think it is healthy """
    mke_nodes = mke.api_nodes()
    """ list of nodes for the mke client """
    unhealthy_node_count = 0
    for node in mke_nodes:
        try:
            assert MKENodeState.READY.match(
                node['Status']['State']), "MKE NODE {} was not in a READY state: {}".format(
                node['ID'], node['Status'])
        except Exception as e:
            unhealthy_node_count += 1
            logger.warn("{}".format(e))

    if unhealthy_node_count == 0:
        logger.info("MKE reports all nodes are healthy")
    elif unhealthy_node_count < 2:
        logger.warning("MKE Reports some nodes are unhappy")
    else:
        logger.error("MKE Reports cluster is unhealthy")
        raise RuntimeError("Cluster is unhealthy, so this test will stop")


def k8s_health(kubeapi, logger):
    """ Does kubernetes think the workload is healthy """

    coreV1Api = kubeapi.get_api('CoreV1Api')
    watch = kubeapi.watch()

    unhealthy_pod_count = 0
    for pod in coreV1Api.list_namespaced_pod(namespace="npods").items:
        if pod.status.phase == "Failed":
            logger.error(
                "Kubernetes reports a pod failed: {}".format(
                    pod.metadata.name))
            unhealthy_pod_count += 1
    if unhealthy_pod_count == 0:
        logger.info("Kubernetes reports all pods as healthy")
    elif unhealthy_pod_count < 2:
        logger.warning("Kubernetes Reports some pods are failed")
    else:
        logger.error("Kubernetes Reports cluster is unhealthy")
        raise RuntimeError("Workload is unhealthy, so this test will stop")

# ------ TEST CASES ---------------------------------------


test_01_500 = _create_scale_and_test_function(
    {'replicas': 500, 'threads': 250})
""" Initial scale up to 500 pods """
test_02_1000 = _create_scale_and_test_function(
    {'replicas': 500, 'threads': 250})
""" Scale up to 1000 pods """
test_03_test = _create_scale_and_test_function(
    {'replicas': 500, 'threads': 250})
""" Scale up to 1500 pods """
test_04_test = _create_scale_and_test_function(
    {'replicas': 500, 'threads': 250})
""" Scale up to 2000 pods """
test_04_test = _create_scale_and_test_function(
    {'replicas': 500, 'threads': 250})
""" Scale up to 2500 pods """
test_05_test = _create_scale_and_test_function(
    {'replicas': 250, 'threads': 125})
""" Scale up to 2750 pods """
test_06_test = _create_scale_and_test_function(
    {'replicas': 250, 'threads': 215})
""" Scale up to 3000 pods """
test_07_test = _create_scale_and_test_function(
    {'replicas': 100, 'threads': 50})
""" Scale up to 3100 pods """
test_08_test = _create_scale_and_test_function(
    {'replicas': 100, 'threads': 50})
""" Scale up to 3200 pods """
test_09_test = _create_scale_and_test_function(
    {'replicas': 100, 'threads': 50})
""" Scale up to 3300 pods """
test_09_test = _create_scale_and_test_function(
    {'replicas': 100, 'threads': 50})
""" Scale up to 3400 pods """
test_09_test = _create_scale_and_test_function(
    {'replicas': 100, 'threads': 50})
""" Scale up to 3500 pods """
test_09_test = _create_scale_and_test_function(
    {'replicas': 100, 'threads': 50})
""" Scale up to 3600 pods """
test_09_test = _create_scale_and_test_function(
    {'replicas': 100, 'threads': 50})
""" Scale up to 3700 pods """
test_09_test = _create_scale_and_test_function(
    {'replicas': 100, 'threads': 50})
""" Scale up to 3800 pods """
test_09_test = _create_scale_and_test_function(
    {'replicas': 100, 'threads': 50})
""" Scale up to 3900 pods """
