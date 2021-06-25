"""

Mirantis MSR health check plugin.

"""
import logging

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.healthcheck import Health, HealthStatus

from .msr_client import MSRAPIClientPlugin, MSRReplicaHealth

logger = logging.getLogger('metta_mirantis.msr_health')


class MSRHealthCheckPlugin:
    """Metta healthcheck plugin that checks on MSR health using an api client."""

    def __init__(self, environment: Environment, instance_id: str, msr_api: MSRAPIClientPlugin):
        """Create a healthcheck plugin for a specific API plugin instance."""
        self.environment = environment
        self.instance_id = instance_id

        self.msr_api = msr_api
        """MSR API plugins which will be used for health checks."""

    def info(self, deep: bool = False):
        """Return information about the plugin."""
        info = {
            'fixtures': {
                'instance_id': self.instance_id
            },
        }

        if deep:
            info['api_plugin'] = self.msr_api.info()

        return info

    def health(self) -> Health:
        """Determine the health of the MSR instance."""
        msr_health = Health(status=HealthStatus.UNKNOWN)

        for test_health_function in [
            self.test_node_health,
            self.test_msr_replica_health,
            self.test_msr_alerts
        ]:
            test_health = test_health_function()
            msr_health.merge(test_health)

        return msr_health

    def test_node_health(self):
        """Test node health."""
        health = Health()

        for node_index in range(self.msr_api.host_count()):
            node_health = self.msr_api.api_health(node=node_index)
            if node_health['Healthy']:
                health.info(f"Node [{node_index}] is healthy")
            else:
                health.error(node_health['Error'])

        return health

    def test_msr_replica_health(self):
        """Test that we can access node information."""
        health = Health()

        status = self.msr_api.api_status()
        replica_health = status['replica_health']

        if replica_health is None:
            health.warning("MSR cluster reports a null replica health. This occurs for MSR on K8s.")
        else:
            for replica_id, replica_health in status['replica_health'].items():
                if not MSRReplicaHealth.OK.match(replica_health):
                    health.error(f"Replica [{replica_id}] did is not READY : {replica_health}")

        return health

    def test_msr_alerts(self):
        """Confirm that we can get alerts."""
        health = Health()

        alerts = self.msr_api.api_alerts()

        for alert in alerts:
            health.warning(f"{alert['id']} {alert['class']}: {alert['message']}"
                           f" {alert['url'] if hasattr(alert, 'url') else ''}")

        return health
