"""

Metta cli plugin for msr.

MSR api client and healthcheck cli plugin.

"""

import requests

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta_cli.base import CliBase, cli_output

from .msr_client import METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID

METTA_MIRANTIS_CLI_MSR_PLUGIN_ID = "mirantis_msr_cli"
""" Mirantis MSR API CLI plugin id """

# this interface is common for all Metta plugins, but CLI plugins underuse it
# pylint: disable=too-few-public-methods


class MSRAPICliPlugin(CliBase):
    """Metta CLI plugin for injecting MSR API Client commands into the cli."""

    def fire(self):
        """Return any MSR CLI command groups."""
        if (
            self._environment.fixtures.get(
                plugin_id=METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID,
                exception_if_missing=False,
            )
            is not None
        ):
            return {"contrib": {"msr": MSRAPICliGroup(self._environment)}}

        return {}


class MSRAPICliGroup:
    """MSR API Client CLI commands."""

    def __init__(self, environment: Environment):
        """Create a new MSR CLI command group."""
        self._environment = environment

    def _select_fixture(self, instance_id: str = ""):
        """Pick a matching fixture in case there are more than one."""
        if instance_id:
            return self._environment.fixtures.get(
                plugin_id=METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID,
                instance_id=instance_id,
            )

        # Get the highest priority fixture
        return self._environment.fixtures.get(
            plugin_id=METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID,
        )

    def info(self, instance_id: str = "", deep: bool = False):
        """Get info about a plugin."""
        fixture = self._select_fixture(instance_id=instance_id)
        return cli_output(fixture.info(deep=deep))

    def health(self, instance_id: str = ""):
        """Get health for the plugin."""
        fixture = self._select_fixture(instance_id=instance_id)
        plugin = fixture.plugin

        health_info = {}
        for health_fixture in plugin.healthchecks():
            health_plugin = health_fixture.plugin
            health_plugin_results = health_plugin.health()
            health_info[health_plugin.instance_id] = {
                "instance_id": health_plugin.instance_id,
                "status": health_plugin_results.status,
                "messages": health_plugin_results.messages,
            }

        return cli_output(health_info)

    def ping(self, instance_id: str = "", node: int = None):
        """Ping an MSR replica."""
        fixture = self._select_fixture(instance_id=instance_id)
        plugin = fixture.plugin
        return cli_output(plugin.api_ping(node=node))

    def pingall(self, instance_id: str = ""):
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

    def nginx_status(self, instance_id: str = "", node: int = None):
        """Get the MSR nginsx status api response."""
        fixture = self._select_fixture(instance_id=instance_id)
        plugin = fixture.plugin
        return cli_output(plugin.api_nginx_status(node=node))

    def version(self, instance_id: str = ""):
        """Get MSR cluster version."""
        fixture = self._select_fixture(instance_id=instance_id)
        plugin = fixture.plugin
        return cli_output(plugin.api_version())

    def status(self, instance_id: str = ""):
        """Get cluster status."""
        fixture = self._select_fixture(instance_id=instance_id)
        plugin = fixture.plugin
        return cli_output(plugin.api_status())

    def features(self, instance_id: str = ""):
        """Get features list."""
        fixture = self._select_fixture(instance_id=instance_id)
        plugin = fixture.plugin
        return cli_output(plugin.api_features())

    def alerts(self, instance_id: str = ""):
        """Get alerts list."""
        fixture = self._select_fixture(instance_id=instance_id)
        plugin = fixture.plugin
        return cli_output(plugin.api_alerts())

    def auth(self, instance_id: str = ""):
        """Get an access token."""
        fixture = self._select_fixture(instance_id=instance_id)
        plugin = fixture.plugin
        # using private method for introspection access
        # pylint: disable=protected-access
        return cli_output(plugin._api_auth())
