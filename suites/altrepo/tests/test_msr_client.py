"""

Test that teh MKE client works

"""
import json
import logging

from mirantis.testing.metta.plugin import Type
from mirantis.testing.metta_mirantis.msr_client import MSRReplicaHealth, METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID

logger = logging.getLogger("test_msr")


def test_launchpad_msr_client(environment_up):
    """ did we get a good msr client """

    # get the mke client.
    # We could get this from the launchpad provisioner if we were worried about
    # which mke client plugin instance we receive,  however there is only one
    # in this case.
    msr_client = environment_up.fixtures.get_plugin(
        type=Type.CLIENT, plugin_id=METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID)


def test_msr_health(environment_up):
    """ test that we can access node information """

    msr_client = environment_up.fixtures.get_plugin(
        type=Type.CLIENT, plugin_id=METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID)

    status = msr_client.api_status()
    for replica_id, replica_health in status['replica_health'].items():
        assert MSRReplicaHealth.OK.match(
            replica_health), "Replica [{}] did is not READY : {}".format(replica_id, replica_health)


def test_launchpad_msr_alerts(environment_up):
    """ check that we can get alerts """

    msr_client = environment_up.fixtures.get_plugin(
        type=Type.CLIENT, plugin_id=METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID)

    alerts = msr_client.api_alerts()

    if len(alerts) > 0:

        for alert in alerts:
            logger.warn(
                "{}: {} [{}]".format(
                    alert['id'],
                    alert['message'],
                    alert['url']))
