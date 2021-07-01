"""

Test that some clients work

"""

import logging
import pytest

from mirantis.testing.metta.environment import Environment

from mirantis.testing.metta_mirantis.msr_client import (
    MSRAPIClientPlugin,
    MSRReplicaHealth,
)
from mirantis.testing.metta_mirantis.mke_client import MKEAPIClientPlugin, MKENodeState

from mirantis.testing.metta_kubernetes.deployment_workload import (
    KubernetesDeploymentWorkloadInstance,
)

logger = logging.getLogger("test_stop")


# pylint: disable=unused-argument
@pytest.mark.order(2)
def test_after_up(environment_after_up: Environment):
    """confirm that phase 2 has started"""
    logger.info("AFTER: environment is confirmed up.")


@pytest.mark.order(2)
def test_kube_workload_still_running(
    stability_workload_instance: KubernetesDeploymentWorkloadInstance,
):
    """did we get a good kubectl client"""
    logger.info(
        "AFTER: Getting K8s test deployment which was run in the 'before' environment."
    )

    namespace = stability_workload_instance.namespace
    name = stability_workload_instance.name

    # The start test sshould have created this workload, so we should be able
    # to find it.
    deployment = stability_workload_instance.read()
    assert deployment is not None, "Did not find the expected sanity workload running"
    logger.info(deployment)

    status = deployment.status
    assert status is not None
    logger.info("Sanity deployment status: %s", status)
    metadata = deployment.metadata
    assert name == metadata.name
    assert namespace == metadata.namespace

    # tear the deployment down
    status = stability_workload_instance.destroy()
    assert status is not None
    assert status.code is None
    logger.info("Sanity deployment destroy status: %s", status)


@pytest.mark.order(2)
def test_mke_api_info(mke_client: MKEAPIClientPlugin):
    """did we get a good mke client"""
    info = mke_client.api_info()
    logger.info("MKE Cluster ID: %s", info["ID"])
    logger.info("--> Warnings : %s", info["Warnings"])


@pytest.mark.order(2)
def test_mke_nodes_health(mke_client: MKEAPIClientPlugin):
    """did we get a good mke client"""
    nodes = mke_client.api_nodes()

    for node in nodes:
        assert MKENodeState.READY.match(
            node["Status"]["State"]
        ), f"MKE NODE {node['ID']} was not in a READY state: {node['Status']}"


@pytest.mark.order(2)
def test_mke_swarminfo_health(mke_client: MKEAPIClientPlugin):
    """Check if MKE thinks it has a healthy swarm."""
    info = mke_client.api_info()

    if "Swarm" in info:
        swarm_info = info["Swarm"]
        assert swarm_info["Nodes"] > 0, "MKE reports no nodes in the cluster"


@pytest.mark.order(2)
def test_msr_client(msr_client: MSRAPIClientPlugin):
    """did we get a good msr client"""
    logger.info("We received a good MSR client.")


@pytest.mark.order(2)
def test_msr_root_health(msr_client: MSRAPIClientPlugin):
    """test the the node specific ping and health checks don't fail"""
    for i in range(0, msr_client.host_count()):
        assert msr_client.api_ping(node=i)
        assert msr_client.api_health(node=i)["Healthy"]

        print(f"{i}: NGINX: {msr_client.api_nginx_status(node=i)}")


@pytest.mark.order(2)
def test_msr_replica_health(msr_client: MSRAPIClientPlugin):
    """test that we can access node information"""
    status = msr_client.api_status()
    for replica_id, replica_health in status["replica_health"].items():
        assert MSRReplicaHealth.OK.match(
            replica_health
        ), f"Replica [{replica_id}] is not READY"


@pytest.mark.order(2)
def test_msr_alerts(msr_client: MSRAPIClientPlugin):
    """check that we can get alerts"""
    alerts = msr_client.api_alerts()

    if len(alerts) > 0:

        for alert in alerts:
            logger.warning(
                "%s: %s [%s]",
                alert["id"],
                alert["message"],
                alert["url"] if "url" in alert else "no-url",
            )
