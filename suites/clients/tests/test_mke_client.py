"""

Test that teh MKE client works

"""
import json
import logging

from mirantis.testing.metta.plugin import Type
from mirantis.testing.metta_mirantis.mke_client import MKENodeState, METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID

logger = logging.getLogger("test_mke")


def test_launchpad_mke_client_id(environment_up):
    """ did we get a good mke client """

    # get the mke client.
    # We could get this from the launchpad provisioner if we were worried about
    # which mke client plugin instance we receive,  however there is only one
    # in this case.
    mke_client = environment_up.fixtures.get_plugin(
        type=Type.CLIENT, plugin_id=METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID)

    info = mke_client.api_info()
    logger.info("MKE Cluster ID: {}".format(info['ID']))
    logger.info("--> Warnings : {}".format(info['Warnings']))


def test_launchpad_mke_nodes(environment_up):
    """ did we get a good mke client """

    mke_client = environment_up.fixtures.get_plugin(
        type=Type.CLIENT, plugin_id=METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID)

    nodes = mke_client.api_nodes()

    for node in nodes:
        assert MKENodeState.READY.match(
            node['Status']['State']), "MKE NODE {} was not in a READY state: {}".format(
            node['ID'], node['Status'])


def test_launchpad_mke_swarminfo(environment_up):
    """ did we get a good mke client """

    mke_client = environment_up.fixtures.get_plugin(
        type=Type.CLIENT, plugin_id=METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID)

    info = mke_client.api_info()

    if 'Swarm' in info:
        swarm_info = info['Swarm']

        assert swarm_info['Nodes'] > 0, "MKE reports no nodes in the cluster"
