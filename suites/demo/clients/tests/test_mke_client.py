"""

Test that some clients work.

Here test the mke client.

"""
import logging

import pytest

from mirantis.testing.metta_mirantis.mke_client import (
    MKENodeState,
    METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID,
)

logger = logging.getLogger("test_clients.mkeapi")


@pytest.fixture(scope="module")
def mke_client(environment_up):
    """Get the mke_api client."""
    # get the mke client.
    # We could get this directly from the provisioner if we were worried about
    # which mke client plugin instance we receive,  however there is only one
    # in this case.
    return environment_up.fixtures.get_plugin(
        plugin_id=METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID,
    )


def test_launchpad_mke_client_id(mke_client):
    """did we get a good mke client"""
    info = mke_client.api_info()
    logger.info("MKE Cluster ID: %s", info["ID"])
    logger.info("--> Warnings : %s", info["Warnings"])


def test_launchpad_mke_nodes(mke_client):
    """Confirm that we get a good mke client."""
    nodes = mke_client.api_nodes()

    for node in nodes:
        assert MKENodeState.READY.match(
            node["Status"]["State"]
        ), f"MKE NODE {node['ID']} was not in a READY state: {node['Status']}"


def test_launchpad_mke_swarminfo(mke_client):
    """Confirm that we get a good mke client."""
    info = mke_client.api_info()
    if "Swarm" in info:
        swarm_info = info["Swarm"]

        assert swarm_info["Nodes"] > 0, "MKE reports no nodes in the cluster"
