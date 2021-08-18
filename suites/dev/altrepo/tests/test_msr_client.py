"""

Test that teh MKE client works

"""

import logging

from mirantis.testing.metta.client import METTA_PLUGIN_INTERFACE_ROLE_CLIENT
from mirantis.testing.metta_mirantis.msr_client import (
    MSRReplicaHealth,
    METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID,
)

logger = logging.getLogger("test_msr")

# this is a test suite, and lazy interpolation is not very strong
# pylint: disable=logging-format-interpolation


def test_launchpad_msr_client(environment_up):
    """did we get a good msr client"""

    # get the mke client.
    # We could get this from the launchpad provisioner if we were worried about
    # which mke client plugin instance we receive,  however there is only one
    # in this case.
    environment_up.fixtures().get_plugin(
        plugin_type=METTA_PLUGIN_INTERFACE_ROLE_CLIENT,
        plugin_id=METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID,
    )


def test_msr_health(environment_up):
    """test that we can access node information"""

    msr_client = environment_up.fixtures().get_plugin(
        plugin_type=METTA_PLUGIN_INTERFACE_ROLE_CLIENT,
        plugin_id=METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID,
    )

    status = msr_client.api_status()
    for replica_id, replica_health in status["replica_health"].items():
        assert MSRReplicaHealth.OK.match(
            replica_health
        ), f"Replica [{replica_id}] did is not READY : {replica_health}"


def test_launchpad_msr_alerts(environment_up):
    """check that we can get alerts"""

    msr_client = environment_up.fixtures().get_plugin(
        plugin_type=METTA_PLUGIN_INTERFACE_ROLE_CLIENT,
        plugin_id=METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID,
    )

    alerts = msr_client.api_alerts()

    if len(alerts) > 0:

        for alert in alerts:
            logger.warning("%s: %s [%s]", alert["id"], alert["message"], alert["url"])
