"""

Test that some clients work

"""

import logging
import pytest

from mirantis.testing.metta.plugin import Type

from mirantis.testing.metta_mirantis.msr_client import MSRReplicaHealth, METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID
from mirantis.testing.metta_mirantis.mke_client import MKENodeState, METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID

logger = logging.getLogger("test_stop")


@pytest.mark.order(2)
def test_after_up(environment_after_up):
    """ confirm that phase 2 has started """
    logger.info("AFTER: environment is confirmed up.")


@pytest.mark.order(2)
def test_kube_workload_still_running(environment_after_up):
    """ did we get a good kubectl client """

    logger.info(
        "AFTER: Getting K8s test deployment which was run in the 'before' environment.")

    sanity_kubernetes_deployment = environment_after_up.fixtures.get_plugin(type=Type.WORKLOAD,
                                                                            instance_id='sanity_kubernetes_deployment')
    instance = sanity_kubernetes_deployment.create_instance(
        environment_after_up.fixtures)

    namespace = instance.namespace
    name = instance.name

    # The start test sshould have created this workload, so we should be able
    # to find it.
    deployment = instance.read()
    assert deployment is not None, "Did not find the expected sanity workload running"
    logger.info(deployment)

    status = deployment.status
    assert status is not None
    logger.info("Sanity deployment status: {}".format(status))
    metadata = deployment.metadata
    assert name == metadata.name
    assert namespace == metadata.namespace

    # tear the deployment down
    status = instance.destroy()
    assert status is not None
    assert status.code is None
    logger.info("Sanity deployment destroy status: {}".format(status))


@pytest.mark.order(2)
def test_mke_api_info(environment_after_up):
    """ did we get a good mke client """

    # get the mke client.
    # We could get this from the launchpad provisioner if we were worried about
    # which mke client plugin instance we receive,  however there is only one
    # in this case.
    mke_client = environment_after_up.fixtures.get_plugin(
        type=Type.CLIENT, plugin_id=METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID)

    info = mke_client.api_info()
    logger.info("MKE Cluster ID: {}".format(info['ID']))
    logger.info("--> Warnings : {}".format(info['Warnings']))


@pytest.mark.order(2)
def test_mke_nodes_health(environment_after_up):
    """ did we get a good mke client """

    mke_client = environment_after_up.fixtures.get_plugin(
        type=Type.CLIENT, plugin_id=METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID)

    nodes = mke_client.api_nodes()

    for node in nodes:
        assert MKENodeState.READY.match(
            node['Status']['State']), "MKE NODE {} was not in a READY state: {}".format(
            node['ID'], node['Status'])


@pytest.mark.order(2)
def test_mke_swarminfo_health(environment_after_up):
    """ did we get a good mke client """

    mke_client = environment_after_up.fixtures.get_plugin(
        type=Type.CLIENT, plugin_id=METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID)

    info = mke_client.api_info()

    if 'Swarm' in info:
        swarm_info = info['Swarm']

        assert swarm_info['Nodes'] > 0, "MKE reports no nodes in the cluster"


@pytest.mark.order(2)
def test_msr_client(environment_after_up):
    """ did we get a good msr client """

    # get the mke client.
    # We could get this from the launchpad provisioner if we were worried about
    # which mke client plugin instance we receive,  however there is only one
    # in this case.
    msr_client = environment_after_up.fixtures.get_plugin(
        type=Type.CLIENT, plugin_id=METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID)


@pytest.mark.order(2)
def test_msr_root_health(environment_after_up):
    """ test the the node specific ping and health checks don't fail """
    msr_client = environment_after_up.fixtures.get_plugin(
        type=Type.CLIENT, plugin_id=METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID)

    for i in range(0, msr_client.host_count()):
        assert msr_client.api_ping(node=i)
        assert msr_client.api_health(node=i)["Healthy"]

        print("{}: NGINX: {}".format(i, msr_client.api_nginx_status(node=i)))


@pytest.mark.order(2)
def test_msr_replica_health(environment_after_up):
    """ test that we can access node information """

    msr_client = environment_after_up.fixtures.get_plugin(
        type=Type.CLIENT, plugin_id=METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID)

    status = msr_client.api_status()
    for replica_id, replica_health in status['replica_health'].items():
        assert MSRReplicaHealth.OK.match(
            replica_health), "Replica [{}] did is not READY : {}".format(replica_id, replica_health)


@pytest.mark.order(2)
def test_msr_alerts(environment_after_up):
    """ check that we can get alerts """

    msr_client = environment_after_up.fixtures.get_plugin(
        type=Type.CLIENT, plugin_id=METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID)

    alerts = msr_client.api_alerts()

    if len(alerts) > 0:

        for alert in alerts:
            logger.warning(
                "{}: {} [{}]".format(
                    alert['id'],
                    alert['message'],
                    alert['url'] if 'url' in alert else 'no-url'))
