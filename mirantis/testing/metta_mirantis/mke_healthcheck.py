"""

Mirantis MKE health check plugin.

"""
import logging

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.healthcheck import Health, HealthStatus

from .mke_client import MKEAPIClientPlugin, MKENodeState

logger = logging.getLogger('metta_mirantis.mke_health')


class MKEHealthCheckPlugin:
    """Metta healthcheck plugin that checks on MKE health using an api client."""

    def __init__(self, environment: Environment, instance_id: str, mke_api: MKEAPIClientPlugin):
        """Create a healthcheck plugin for a specific API plugin instance."""
        self.environment = environment
        self.instance_id = instance_id

        self.mke_api = mke_api
        """MKE API plugins which will be used for health checks."""

    def info(self, deep: bool = False):
        """Return information about the plugin."""
        info = {
            'fixtures': {
                'instance_id': self.instance_id
            },
        }

        if deep:
            info['api_plugin'] = self.mke_api.info()

        return info

    def health(self) -> Health:
        """Determine the health of the MKE instance."""
        mke_health = Health(status=HealthStatus.UNKNOWN)

        for test_health_function in [
            self.test_launchpad_self_mke_api_id,
            self.test_launchpad_mke_nodes,
            self.test_launchpad_mke_swarminfo
        ]:
            test_health = test_health_function()
            mke_health.merge(test_health)

        return mke_health

    def test_launchpad_self_mke_api_id(self):
        """Did we get a good mke client."""
        health = Health()

        info = self.mke_api.api_info()

        health.info(f"MKE Cluster ID: {info['ID']}")

        no_warnings = True
        if hasattr(info, 'Warnings'):
            for warning in info['Warnings']:
                health.warning(f"Warning : {warning}")
                no_warnings = False

        if no_warnings:
            health.info("MKE reports no warnings.")

        return health

    def test_launchpad_mke_nodes(self):
        """Confirm that we get a good mke client."""
        health = Health()

        nodes = self.mke_api.api_nodes()

        all_healthy = True
        for node in nodes:
            if not MKENodeState.READY.match(node['Status']['State']):
                health.warning(f"MKE NODE {node['ID']} was not in a READY state: {node['Status']}")
                all_healthy = False

        if all_healthy:
            health.info("MKE reports all nodes are healthy.")

        return health

    def test_launchpad_mke_swarminfo(self):
        """Confirm that we get a good mke client."""
        health = Health()

        info = self.mke_api.api_info()

        swarm_healthy = True
        if 'Swarm' in info:
            swarm_info = info['Swarm']

            if swarm_info['Nodes'] == 0:
                health.error("MKE reports no nodes in the cluster")
                swarm_healthy = False

        if swarm_healthy:
            health.info("MKE reports swarm nodes are healthy.")

        return health
