"""

Test that some clients work.

Here test the mke client.

"""
import logging

import pytest

from mirantis.testing.metta_mirantis.msr_client import (
    MSRReplicaHealth,
    METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID,
)


logger = logging.getLogger("test_clients.mkeapi")


@pytest.fixture(scope="module")
def msr_client(environment_up):
    """Get the msr_api client."""
    # get the msr client.
    # We could get this directly from the provisioner if we were worried about
    # which mke client plugin instance we receive,  however there is only one
    # in this case.
    return environment_up.fixtures.get_plugin(
        plugin_id=METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID,
    )


def test_launchpad_msr_client(msr_client):
    """Check that we get a good msr client."""
    msr_client.api_status()


def test_msr_health(msr_client):
    """Test that we can access node information."""
    status = msr_client.api_status()
    for replica_id, replica_health in status["replica_health"].items():
        assert MSRReplicaHealth.OK.match(
            replica_health
        ), f"Replica [{replica_id}] did is not READY : {replica_health}"


def test_launchpad_msr_alerts(msr_client):
    """Confirm that we can get alerts."""
    alerts = msr_client.api_alerts()

    if len(alerts) > 0:

        for alert in alerts:
            logger.warning("%s: %s [%s]", alert["id"], alert["message"], alert["url"])
