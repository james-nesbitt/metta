"""

Metta cli plugin for MKE.

Metta cli handling for mke api clients, and perhaps also mke healthcheck
plugins as well.

"""

import requests

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.client import METTA_PLUGIN_TYPE_CLIENT
from mirantis.testing.metta_cli.base import CliBase, cli_output

from .mke_client import METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID


# this interface is common for all Metta plugins, but CLI plugins underuse it
# pylint: disable=too-few-public-methods


class MKEAPICliPlugin(CliBase):
    """Metta CLI plugin which injects the MKE API Client CLI commands."""

    def fire(self):
        """Return a dict of commands for MKE API Clients."""
        if len(self.environment.fixtures.filter(
                plugin_type=METTA_PLUGIN_TYPE_CLIENT,
                plugin_id=METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID,
                exception_if_missing=False)) > 0:

            return {
                'contrib': {
                    'mke': MKEAPICliGroup(self.environment)
                }
            }

        return {}


class MKEAPICliGroup():
    """Metta CLI plugin which provides the MKE API Client CLI commands."""

    def __init__(self, environment: Environment):
        """Create new cli group object."""
        self.environment = environment

    def _select_fixture(self, instance_id: str = ''):
        """Pick a matching fixture in case there are more than one."""
        if instance_id:
            return self.environment.fixtures.get(
                plugin_type=METTA_PLUGIN_TYPE_CLIENT,
                plugin_id=METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID,
                instance_id=instance_id)

        # Get the highest priority fixture
        return self.environment.fixtures.get(
            plugin_type=METTA_PLUGIN_TYPE_CLIENT, plugin_id=METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID)

    def info(self, instance_id: str = '', deep: bool = False):
        """Get info about a plugin."""
        fixture = self._select_fixture(instance_id=instance_id)
        plugin = fixture.plugin

        info = {
            'fixture': {
                'plugin_type': fixture.plugin_type,
                'plugin_id': fixture.plugin_id,
                'instance_id': fixture.instance_id,
                'priority': fixture.priority,
            }
        }

        info.update(plugin.info(deep))

        return cli_output(info)

    def health(self, instance_id: str = ''):
        """Get ihealth for the plugin."""
        fixture = self._select_fixture(instance_id=instance_id)
        plugin = fixture.plugin

        health_info = {}
        for health_fixture in plugin.healthchecks():
            health_plugin = health_fixture.plugin
            health_plugin_results = health_plugin.health()
            health_info[health_plugin.instance_id] = {
                'instance_id': health_plugin.instance_id,
                'status': health_plugin_results.status,
                'messages': health_plugin_results.messages
            }

        return cli_output(health_info)

    def version(self, instance_id: str = ''):
        """Get MKE Version."""
        fixture = self._select_fixture(instance_id=instance_id)
        plugin = fixture.plugin
        return cli_output(plugin.api_version())

    def ping(self, instance_id: str = '', node: int = None):
        """Check if we can ping MKE."""
        fixture = self._select_fixture(instance_id=instance_id)
        plugin = fixture.plugin
        return "OK" if plugin.api_ping(node) else "FAIL"

    def pingall(self, instance_id: str = ''):
        """Check if we can ping all of the nodes directly."""
        fixture = self._select_fixture(instance_id=instance_id)
        plugin = fixture.plugin
        ping = {}
        for index in range(0, plugin.host_count()):
            try:
                plugin.api_ping(index)
                # pylint: disable=protected-access
                ping[plugin._node_address(index)] = True
            except requests.exceptions.RequestException:
                # pylint: disable=protected-access
                ping[plugin._node_address(index)] = False

        return cli_output(ping)

    # pylint: disable=invalid-name
    def id(self, instance_id: str = ''):
        """Get auth id from MKE."""
        fixture = self._select_fixture(instance_id=instance_id)
        plugin = fixture.plugin
        return cli_output(plugin.api_id())

    def nodes(self, instance_id: str = '', node_id: str = ''):
        """List swarm nodes."""
        fixture = self._select_fixture(instance_id=instance_id)
        plugin = fixture.plugin
        return cli_output(plugin.api_nodes(node_id))

    def services(self, instance_id: str = '', service_id: str = ''):
        """List swarm services."""
        fixture = self._select_fixture(instance_id=instance_id)
        plugin = fixture.plugin
        return cli_output(plugin.api_services(service_id))

    def tasks(self, instance_id: str = '', task_id: str = ''):
        """List swarm tasks."""
        fixture = self._select_fixture(instance_id=instance_id)
        plugin = fixture.plugin
        if task_id:
            return cli_output(plugin.api_task(task_id))
        return cli_output(plugin.api_tasks())

    def tomlconfig(self, instance_id: str = ''):
        """Get the toml config."""
        fixture = self._select_fixture(instance_id=instance_id)
        plugin = fixture.plugin
        return cli_output(plugin.api_ucp_configtoml_get())

    def tomlconfig_set(self, table: str, key: str,
                       value: str, instance_id: str = ''):
        """Set a single toml config value."""
        fixture = self._select_fixture(instance_id=instance_id)
        plugin = fixture.plugin

        data = plugin.api_ucp_configtoml_get()
        data[table][key] = value
        return cli_output(plugin.api_ucp_configtoml_put(data))

    def metricsdiscovery(self, instance_id: str = ''):
        """Get the api metrics-discover."""
        fixture = self._select_fixture(instance_id=instance_id)
        plugin = fixture.plugin
        return cli_output(plugin.api_metrics_discovery())

    def metrics(self, instance_id: str = ''):
        """Get the toml config."""
        fixture = self._select_fixture(instance_id=instance_id)
        plugin = fixture.plugin
        return cli_output(plugin.api_metrics_discovery())

    # we violate private method to provide manual access on the cli
    # pylint: disable=protected-access
    def auth(self, instance_id: str = ''):
        """Retrieve auth headers."""
        fixture = self._select_fixture(instance_id=instance_id)
        plugin = fixture.plugin
        return cli_output(plugin._auth_headers())

    def bundle(self, instance_id: str = ''):
        """Output bundle contents."""
        fixture = self._select_fixture(instance_id=instance_id)
        plugin = fixture.plugin
        return cli_output(plugin.api_read_bundle_meta())

    def get_bundle(self, instance_id: str = '', force: bool = False):
        """Get the client bundle."""
        fixture = self._select_fixture(instance_id=instance_id)
        plugin = fixture.plugin
        plugin.api_get_bundle(force=force)
        return cli_output(plugin.api_read_bundle_meta())
