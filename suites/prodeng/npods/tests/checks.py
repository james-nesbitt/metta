"""

NPods health detection.

Various functions used to determine if a cluster is healthy.

"""
import logging
import time

from mirantis.testing.metta_mirantis.mke_client import MKENodeState

logger = logging.getLogger("npods-test")
""" test-suite logger """

# It is convenient to use the same name to allow a default fallback.
# pylint: disable=redefined-outer-name


# pylint: disable=too-many-arguments,unused-argument
def stability_test(environment, mke, kubeapi, npods_config, logger, period, duration):
    """Run a stability test on the cluster.

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
    start = time.time()
    timeout = start + duration

    index = 1
    logger.info("Stability tests: starting health-check")
    # wait for the first period, to allow a system to stabilize before testing
    time.sleep(period)
    while time.time() < timeout:
        cycle_start = time.time()
        elapsed = int(cycle_start - start)

        logger.info("Cycle %s [%s] starting", index, elapsed)

        # for event in watch.stream(core_v1_api.list_namespaced_pod,
        #                           namespace='npods', timeout_seconds=period):
        #     logger.info("Event: %s %s" % (event['type'], event['object'].metadata.name))

        mke_health(mke, logger)
        k8s_health(kubeapi, logger)

        cycle_elapsed = int(time.time() - cycle_start)
        cycle_remaining = int(period - cycle_elapsed) if period > cycle_elapsed else 0

        time.sleep(cycle_remaining)
        index += 1


def mke_health(mke, logger):
    """Check if MKE thinks it is healthy."""
    mke_nodes = mke.api_nodes()
    """ list of nodes for the mke client """
    unhealthy_node_count = 0
    for node in mke_nodes:
        if not MKENodeState.READY.match(node["Status"]["State"]):
            logger.warning(
                "MKE NODE %s was not in a READY state: %s", node["ID"], node["Status"]
            )
            unhealthy_node_count += 1

    if unhealthy_node_count == 0:
        logger.info("MKE reports all nodes are healthy")
    elif unhealthy_node_count < 2:
        logger.warning("MKE Reports some nodes are unhappy")
    else:
        logger.error("MKE Reports cluster is unhealthy")
        raise RuntimeError("Cluster is unhealthy, so this test will stop")


def k8s_health(kubeapi, logger):
    """Check if kubernetes thinks the workload is healthy."""
    core_v1_api = kubeapi.get_api("CoreV1Api")

    unhealthy_pod_count = 0
    for pod in core_v1_api.list_namespaced_pod(namespace="npods").items:
        if pod.status.phase == "Failed":
            logger.error("Kubernetes reports a pod failed: %s", pod.metadata.name)
            unhealthy_pod_count += 1
    if unhealthy_pod_count == 0:
        logger.info("Kubernetes reports all pods as healthy")
    elif unhealthy_pod_count < 2:
        logger.warning("Kubernetes Reports some pods are failed")
    else:
        logger.error("Kubernetes Reports cluster is unhealthy")
        raise RuntimeError("Workload is unhealthy, so this test will stop")
