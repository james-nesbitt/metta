"""

Metta CLI : HealthCheck commands.

Various commands that allow introspection of healthcheck plugins/fixtures and
their contents.

"""
import logging


from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.healthcheck import METTA_PLUGIN_TYPE_HEALTHCHECK

from .base import CliBase, cli_output

logger = logging.getLogger('metta.cli.healthcheck')


# this interface is common for all Metta plugins, but CLI plugins underuse it
# pylint: disable=too-few-public-methods
class HealthcheckCliPlugin(CliBase):
    """Fire command/group generator for healthcheck commands."""

    def fire(self):
        """Return a dict of commands."""
        return {
            'healthcheck': HealthcheckGroup(self.environment)
        }


class HealthcheckGroup():
    """Base Fire command group for healthcheck commands."""

    def __init__(self, environment: Environment):
        """Create CLI command group."""
        self.environment = environment

    def list(self, raw: bool = False):
        """List all healthchecks."""
        healthcheck_list = [
            fixture.plugin.instance_id for fixture in self.environment.fixtures.filter(
                plugin_type=METTA_PLUGIN_TYPE_HEALTHCHECK)]

        if raw:
            return list
        return cli_output(healthcheck_list)

    def health(self, instance_id: str = ''):
        """Output health status of healtchecks."""
        if instance_id:
            healthchecks = self.environment.fixtures.filter(
                plugin_type=METTA_PLUGIN_TYPE_HEALTHCHECK,
                instance_id=instance_id)
        else:
            healthchecks = self.environment.fixtures.filter(
                plugin_type=METTA_PLUGIN_TYPE_HEALTHCHECK)

        health_info = {}
        for health_fixture in healthchecks:
            health_plugin = health_fixture.plugin
            health_plugin_results = health_plugin.health()
            health_info[health_plugin.instance_id] = {
                'instance_id': health_plugin.instance_id,
                'status': health_plugin_results.status,
                'messages': health_plugin_results.messages
            }

        return cli_output(health_info)

    def _select_healthcheck(self, instance_id: str = ''):
        """Pick a matching healthcheck."""
        if instance_id:
            return self.environment.fixtures.get(plugin_type=METTA_PLUGIN_TYPE_HEALTHCHECK,
                                                 instance_id=instance_id)
        # Get the highest priority healthcheck
        return self.environment.fixtures.get(plugin_type=METTA_PLUGIN_TYPE_HEALTHCHECK)
