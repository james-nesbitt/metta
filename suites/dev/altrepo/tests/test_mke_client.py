"""

Test that teh MKE client works

"""

import logging


from mirantis.testing.metta.client import METTA_PLUGIN_INTERFACE_ROLE_CLIENT
from mirantis.testing.metta_mirantis.mke_client import (
    MKENodeState,
    METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID,
)

logger = logging.getLogger("test_mke")

# this is a test suite, and lazy interpolation is not very strong
# pylint: disable=logging-format-interpolation


def test_launchpad_mke_client_id(environment_up):
    """did we get a good mke client"""

    # get the mke client.
    # We could get this from the launchpad provisioner if we were worried about
    # which mke client plugin instance we receive,  however there is only one
    # in this case.
    mke_client = environment_up.fixtures.get_plugin(
        plugin_type=METTA_PLUGIN_INTERFACE_ROLE_CLIENT,
        plugin_id=METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID,
    )

    info = mke_client.api_info()
    logger.info(f"MKE Cluster ID: {info['ID']}")
    logger.info(f"--> Warnings : {info['Warnings']}")


def test_launchpad_mke_nodes(environment_up):
    """did we get a good mke client"""

    mke_client = environment_up.fixtures.get_plugin(
        plugin_type=METTA_PLUGIN_INTERFACE_ROLE_CLIENT,
        plugin_id=METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID,
    )

    nodes = mke_client.api_nodes()

    for node in nodes:
        assert MKENodeState.READY.match(
            node["Status"]["State"]
        ), f"MKE NODE {node['ID']} was not in a READY state: {node['Status']}"


def test_launchpad_mke_swarminfo(environment_up):
    """did we get a good mke client"""

    mke_client = environment_up.fixtures.get_plugin(
        plugin_type=METTA_PLUGIN_INTERFACE_ROLE_CLIENT,
        plugin_id=METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID,
    )

    info = mke_client.api_info()

    if "Swarm" in info:
        swarm_info = info["Swarm"]

        assert swarm_info["Nodes"] > 0, "MKE reports no nodes in the cluster"
