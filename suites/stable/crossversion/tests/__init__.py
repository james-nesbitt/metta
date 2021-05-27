"""

Cross version testing package

"""
import logging
import json

import pytest

from configerus.loaded import LOADED_KEY_ROOT

from mirantis.testing.metta import get_environment
from mirantis.testing.metta.provisioner import METTA_PLUGIN_TYPE_PROVISIONER
from mirantis.testing.metta.client import METTA_PLUGIN_TYPE_CLIENT
from mirantis.testing.metta_common import METTA_PLUGIN_ID_PROVISIONER_COMBO
from mirantis.testing.metta_launchpad import METTA_LAUNCHPAD_PROVISIONER_PLUGIN_ID
from mirantis.testing.metta_mirantis.mke_client import (MKENodeState,
                                                        METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID)
from mirantis.testing.metta_mirantis.msr_client import (MSRReplicaHealth,
                                                        METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID)


logger = logging.getLogger("base")


class EnvManager:
    """Base testing class that knows how to detect stability in a cluster."""

    __test__ = False

    def __init__(self, env_name: str):
        """Set the environment name to be retrieved."""
        self.env_name = env_name
        """ environment name used for version testing """

    def get_env_in_state(self, state: str = None):
        """Inject an environment into the object."""
        environment = get_environment(self.env_name)
        environment.set_state(state)

        variables = environment.config.load('variables')
        logger.info("%s::%s --> variables: %s", self.env_name, state,
                    json.dumps(variables.get(LOADED_KEY_ROOT), indent=2))

        return environment

    def install(self, environment):
        """Bring up all provisioners as needed."""
        combo_provisioner = environment.fixtures.get_plugin(
            plugin_type=METTA_PLUGIN_TYPE_PROVISIONER, plugin_id=METTA_PLUGIN_ID_PROVISIONER_COMBO)
        combo_provisioner.prepare()
        try:
            combo_provisioner.apply()
        # pylint: disable=broad-except
        except Exception as err:
            logger.error("Provisioner installation failed.  Tearing down the resources now: %s",
                         err)
            self.destroy(environment)
            pytest.exit('Provisioner failed to install')

    def upgrade(self, environment):
        """Upgrade the environment to the second state.

        @NOTE we only need launchpad to re-install for an upgrade
        """
        launchpad_provisioner = environment.fixtures.get_plugin(
            plugin_type=METTA_PLUGIN_TYPE_PROVISIONER,
            plugin_id=METTA_LAUNCHPAD_PROVISIONER_PLUGIN_ID)

        try:
            launchpad_provisioner.apply()
        # pylint: disable=broad-except
        except BaseException:
            logger.error("Provisioner upgrade failed.  Tearing down the resources now")
            self.destroy(environment)
            pytest.exit('Provisioner failed to upgrade')

    # pylint: disable=no-self-use
    def destroy(self, environment):
        """Destroy all created resources."""
        combo_provisioner = environment.fixtures.get_plugin(
            plugin_type=METTA_PLUGIN_TYPE_PROVISIONER,
            plugin_id=METTA_PLUGIN_ID_PROVISIONER_COMBO)
        combo_provisioner.destroy()


class TestBase:
    """A collection of reusable tests."""

    __test__ = False

    # this is a base class, to exend test classes easily
    # pylint: disable=no-self-use

    # ----- MKE TESTS ---------------------------------------------------------

    def mke_all(self, environment):
        """Run all of the MKE tests."""
        self.mke_client_id(environment)
        self.mke_nodes_health(environment)
        self.mke_swarminfo_health(environment)

    def _mke_client_from_env(self, environment):
        """Return the mke client from the environment."""
        # get the mke client.
        # We could get this from the launchpad provisioner if we were worried about
        # which mke client plugin instance we receive,  however there is only one
        # in this case.
        return environment.fixtures.get_plugin(
            plugin_type=METTA_PLUGIN_TYPE_CLIENT,
            plugin_id=METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID)

    def mke_client_id(self, environment):
        """Check that we got a good mke client that can connect to the MKE API."""
        mke_client = self._mke_client_from_env(environment)

        info = mke_client.api_info()
        logger.info("MKE Cluster ID: %s", info['ID'])
        logger.info("--> Warnings : %s", info['Warnings'])

    def mke_nodes_health(self, environment):
        """Check if the mke nodes healthy, do they have a healthy node state."""
        mke_client = self._mke_client_from_env(environment)

        nodes = mke_client.api_nodes()

        for node in nodes:
            assert MKENodeState.READY.match(node['Status']['State']), \
                f"MKE NODE {node['ID']} was not in a READY state: {node['Status']}"

    def mke_swarminfo_health(self, environment):
        """Check if MKE API indicate a nood number of nodes in the swarm (if swarm is used)."""
        mke_client = self._mke_client_from_env(environment)

        info = mke_client.api_info()

        if 'Swarm' in info:
            swarm_info = info['Swarm']

            assert swarm_info['Nodes'] > 0, "MKE reports no nodes in the cluster"

    # ----- MSR TESTS ---------------------------------------------------------

    def msr_all(self, environment):
        """Run all of the MSR tests."""
        self.msr_client(environment)
        self.msr_root_health(environment)
        self.msr_replica_health(environment)
        self.msr_alerts(environment)

    def _msr_client_from_env(self, environment):
        """Return the msr client from the environment."""
        # get the mke client.
        # We could get this from the launchpad provisioner if we were worried about
        # which mke client plugin instance we receive,  however there is only one
        # in this case.
        return environment.fixtures.get_plugin(
            plugin_type=METTA_PLUGIN_TYPE_CLIENT, plugin_id=METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID)

    def msr_client(self, environment):
        """Check that we get a good msr client."""
        self._msr_client_from_env(environment)

    def msr_root_health(self, environment):
        """Test the the node specific ping and health checks don't fail."""
        msr_client = self._msr_client_from_env(environment)

        for i in range(0, msr_client.host_count()):
            assert msr_client.api_ping(node=i)
            assert msr_client.api_health(node=i)["Healthy"]

            print(f"{i}: NGINX: {msr_client.api_nginx_status(node=i)}")

    def msr_replica_health(self, environment):
        """Test that we can access node information."""
        msr_client = self._msr_client_from_env(environment)

        status = msr_client.api_status()
        for replica_id, replica_health in status['replica_health'].items():
            assert MSRReplicaHealth.OK.match(replica_health), \
                f"Replica [{replica_id}] did is not READY : {replica_health}"

    def msr_alerts(self, environment):
        """Check that we can get alerts."""
        msr_client = self._msr_client_from_env(environment)

        # this might produce an exception which would fail the test
        alerts = msr_client.api_alerts()

        if len(alerts) > 0:

            for alert in alerts:
                # we don't actually fail the test on alerts, but we do log
                # then in case they warrant a manual test failure.
                logger.warning("%s: %s [%s]", alert['id'], alert['message'],
                               alert['url'] if 'url' in alert else 'no-url')
