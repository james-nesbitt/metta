"""

Metta CLI plugin for launchpad

Provided CLI commands that allow interacting with launchpad plugins.
CLI commands exist for both provisioner and direct client plugins, with
some overlap existing.

"""

import logging
from typing import List, Dict

import yaml

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta_cli.base import CliBase, cli_output

from .provisioner import (
    LaunchpadProvisionerPlugin,
    METTA_LAUNCHPAD_PROVISIONER_PLUGIN_ID,
)
from .client import (
    LaunchpadClientPlugin,
    METTA_LAUNCHPAD_CLIENT_PLUGIN_ID,
)

logger = logging.getLogger("metta.cli.launchpad")

METTA_LAUNCHPAD_CLI_PLUGIN_ID = "metta_launchpad_cli"
""" metta plugin_id for the launchpad cli plugin """


# this interface is common for all Metta plugins, but CLI plugins underuse it
# pylint: disable=too-few-public-methods
class LaunchpadCliPlugin(CliBase):
    """Fire command/group generator for launchpad plugin commands."""

    def fire(self):
        """Return a dict of commands.

        Don't return any commands if there are no plugind available

        """
        commands: Dict[str, object] = {}

        if (
            self._environment.fixtures.get(
                plugin_id=METTA_LAUNCHPAD_CLIENT_PLUGIN_ID,
                exception_if_missing=False,
            )
            is not None
        ):
            commands["launchpad"] = LaunchpadClientGroup(self._environment)

        return commands


class LaunchpadClientGroup:
    """Base Fire command group for launchpad client cli commands."""

    def __init__(self, environment: Environment):
        """Create launchpad command list object."""
        self._environment = environment

        if (
            self._environment.fixtures.get(
                plugin_id=METTA_LAUNCHPAD_PROVISIONER_PLUGIN_ID,
                exception_if_missing=False,
            )
            is not None
        ):
            self.provisioner = LaunchpadProvisionerGroup(self._environment)

    def _select_client(self, instance_id: str = "") -> LaunchpadClientPlugin:
        """Pick a matching client."""
        if instance_id:
            return self._environment.fixtures.get(
                plugin_id=METTA_LAUNCHPAD_CLIENT_PLUGIN_ID,
                instance_id=instance_id,
            )

        # Get the highest priority client
        return self._environment.fixtures.get(plugin_id=METTA_LAUNCHPAD_CLIENT_PLUGIN_ID)

    def info(self, client: str = "", deep: bool = False):
        """Get info about a client plugin."""
        fixture = self._select_client(instance_id=client)
        return cli_output(fixture.info(deep=deep))

    def hosts(self, client: str = "", deep: bool = False):
        """List the hosts in the cluster/"""
        fixture = self._select_client(instance_id=client)
        plugin = fixture.plugin
        return cli_output(plugin.host_list(deep=deep))

    def exec(self, cmd: str, client: str = "", host: int = 0):
        """Exec a command."""
        client_plugin = self._select_client(instance_id=client).plugin
        return client_plugin.exec(host_index=host, cmds=cmd.split(" "))

    def connect(self, client: str = "", host: int = 0):
        """Exec a command."""
        client_plugin = self._select_client(instance_id=client).plugin
        client_plugin.exec_interactive(host_index=host, cmds=[])

    def client_config(self, client: str = ""):
        """Get the rendered config from the client."""
        client_plugin = self._select_client(instance_id=client).plugin
        return cli_output(client_plugin.describe_config())

    def version(self, client: str = ""):
        """Output a launchpad cli report."""
        client_plugin = self._select_client(instance_id=client).plugin
        client_plugin.client.version()

    def describe(self, report: str, client: str = ""):
        """Output a launchpad cli report."""
        client_plugin = self._select_client(instance_id=client).plugin
        client_plugin.client.describe(report)

    # pylint: disable=redefined-builtin
    def fixtures(
        self,
        client: str = "",
        plugin_id: str = "",
        interfaces: List[str] = None,
        instance_id: str = "",
    ):
        """List all outputs."""
        client_plugin = self._select_client(instance_id=client).plugin

        fixture_list = [
            fixture.info()
            for fixture in client_plugin.fixtures.filter(
                interfaces=interfaces, plugin_id=plugin_id, instance_id=instance_id
            )
        ]

        return cli_output(fixture_list)

    def config_file(self, client: str = ""):
        """Dump the config file."""
        client_plugin = self._select_client(instance_id=client).plugin

        try:
            with open(client_plugin.config_file) as config_file:
                config_contents = yaml.load(config_file)
        except FileNotFoundError as err:
            raise ValueError("No config file was found") from err

        return cli_output(config_contents)

    def write_config(self, client: str = ""):
        """Write config to file."""
        client_plugin = self._select_client(instance_id=client).plugin
        # access private method for introspection
        # pylint: disable=protected-access
        client_plugin._write_launchpad_file()

    def client_bundle(self, client: str = "", user: str = "admin", reload: bool = False):
        """Tell Launchpad to download the client bundle."""
        client_plugin = self._select_client(instance_id=client)
        plugin = client_plugin.plugin

        logger.info("Downloading client bungle for user: %s", user)
        try:
            # access private method for manual interaction
            # pylint: disable=protected-access
            bundle = plugin._mke_client_bundle(user=user, reload=reload)
        except Exception as err:
            raise Exception("Launchpad command failed.") from err

        return cli_output(bundle)

    def apply(self, client: str = ""):
        """Run client apply."""
        client_plugin = self._select_client(instance_id=client).plugin
        client_plugin.apply()

    def reset(self, client: str = ""):
        """Run client destroy."""
        client_plugin = self._select_client(instance_id=client).plugin
        client_plugin.reset()


class LaunchpadProvisionerGroup:
    """Launchpad cli commands."""

    def __init__(self, environment: Environment):
        """Create launchpad command list object."""
        self._environment = environment

    def _select_provisioner(self, instance_id: str = "") -> LaunchpadProvisionerPlugin:
        """Pick a matching provisioner."""
        if instance_id:
            return self._environment.fixtures.get(
                plugin_id=METTA_LAUNCHPAD_PROVISIONER_PLUGIN_ID,
                instance_id=instance_id,
            )

        # Get the highest priority provisioner
        return self._environment.fixtures.get(plugin_id=METTA_LAUNCHPAD_PROVISIONER_PLUGIN_ID)

    def info(self, provisioner: str = "", deep: bool = False):
        """Get info about a provisioner plugin."""
        fixture = self._select_provisioner(instance_id=provisioner)
        return cli_output(fixture.info(deep=deep))

    def prepare(self, provisioner: str = ""):
        """Run provisioner prepare."""
        provisioner_plugin = self._select_provisioner(instance_id=provisioner).plugin
        provisioner_plugin.prepare()

    def apply(self, provisioner: str = ""):
        """Run provisioner apply."""
        provisioner_plugin = self._select_provisioner(instance_id=provisioner).plugin
        provisioner_plugin.apply()

    def destroy(self, provisioner: str = ""):
        """Run provisioner destroy."""
        provisioner_plugin = self._select_provisioner(instance_id=provisioner).plugin
        provisioner_plugin.destroy()
