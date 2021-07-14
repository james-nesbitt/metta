"""

Metta CLI plugin for launchpad

Provided CLI commands that allow interacting with launchpad as a provisioner,
examining launchpad config and more.

"""

import logging
from typing import List

import yaml

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta_cli.base import CliBase, cli_output

from .provisioner import (
    LaunchpadProvisionerPlugin,
    METTA_LAUNCHPAD_PROVISIONER_PLUGIN_ID,
)

logger = logging.getLogger("metta.cli.launchpad")

METTA_LAUNCHPAD_CLI_PLUGIN_ID = "metta_launchpad_cli"
""" metta plugin_id for the launchpad cli plugin """


# this interface is common for all Metta plugins, but CLI plugins underuse it
# pylint: disable=too-few-public-methods
class LaunchpadCliPlugin(CliBase):
    """Fire command/group generator for launchpad plugin commands."""

    def fire(self):
        """Return CLI command group."""
        if (
            self._environment.fixtures.get(
                plugin_id=METTA_LAUNCHPAD_PROVISIONER_PLUGIN_ID,
                exception_if_missing=False,
            )
            is not None
        ):

            return {"contrib": {"launchpad": LaunchpadGroup(self._environment)}}

        return {}


class LaunchpadGroup:
    """Base Fire command group for launchpad cli commands."""

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
        return self._environment.fixtures.get(
            plugin_id=METTA_LAUNCHPAD_PROVISIONER_PLUGIN_ID
        )

    def info(self, provisioner: str = "", deep: bool = False):
        """Get info about a provisioner plugin."""
        fixture = self._select_provisioner(instance_id=provisioner)
        return cli_output(fixture.info(deep=deep))

    def hosts(self, provisioner: str = "", deep: bool = False):
        """List the hosts in the cluster/"""
        fixture = self._select_provisioner(instance_id=provisioner)
        plugin = fixture.plugin
        client = plugin.client

        config = client.describe_config()

        if deep:
            host_list = config["spec"]["hosts"]
        else:
            host_list = []
            for host in config["spec"]["hosts"]:
                list_host = {"role": host["role"]}
                if "ssh" in host:
                    list_host.update(
                        {"is_windows": False, "address": host["ssh"]["address"]}
                    )
                if "winrm" in host:
                    list_host.update(
                        {"is_windows": True, "address": host["winrm"]["address"]}
                    )

                host_list.append(list_host)

        return cli_output(host_list)

    def exec(self, cmd: str, provisioner: str = "", host: int = 0):
        """Exec a command."""
        fixture = self._select_provisioner(instance_id=provisioner)
        plugin = fixture.plugin
        client = plugin.client

        cmds = cmd.split(" ")

        client.exec(host_index=host, cmds=cmds)

    def exec_interactive(self, cmd: str, provisioner: str = "", host: int = 0):
        """Exec a command."""
        fixture = self._select_provisioner(instance_id=provisioner)
        plugin = fixture.plugin
        client = plugin.client

        cmds = cmd.split(" ")

        client.exec_interactive(host_index=host, cmds=cmds)

    def connect(self, provisioner: str = "", host: int = 0):
        """Exec a command."""
        fixture = self._select_provisioner(instance_id=provisioner)
        plugin = fixture.plugin
        client = plugin.client

        client.exec_interactive(host_index=host, cmds=[])

    def client_config(self, provisioner: str = ""):
        """Get the rendered config from the client."""
        fixture = self._select_provisioner(instance_id=provisioner)
        plugin = fixture.plugin
        client = plugin.client

        return cli_output(client.describe_config())

    def version(self, provisioner: str = ""):
        """Output a launchpad cli report."""
        provisioner_plugin = self._select_provisioner(instance_id=provisioner).plugin
        provisioner_plugin.client.version()

    def describe(self, report: str, provisioner: str = ""):
        """Output a launchpad cli report."""
        provisioner_plugin = self._select_provisioner(instance_id=provisioner).plugin
        provisioner_plugin.client.describe(report)

    # pylint: disable=redefined-builtin
    def fixtures(
        self,
        provisioner: str = "",
        plugin_id: str = "",
        interfaces: List[str] = None,
        instance_id: str = "",
    ):
        """List all outputs."""
        provisioner_plugin = self._select_provisioner(instance_id=provisioner).plugin

        fixture_list = [
            {
                "plugin_id": fixture.plugin_id,
                "interfaces": fixture.interfaces,
                "instance_id": fixture.instance_id,
                "priority": fixture.priority,
            }
            for fixture in provisioner_plugin.fixtures.filter(
                interfaces=interfaces, plugin_id=plugin_id, instance_id=instance_id
            )
        ]

        return cli_output(fixture_list)

    def config_file(self, provisioner: str = ""):
        """Dump the config file."""
        provisioner_plugin = self._select_provisioner(instance_id=provisioner).plugin

        try:
            with open(provisioner_plugin.config_file) as config_file:
                config_contents = yaml.load(config_file)
        except FileNotFoundError as err:
            raise ValueError("No config file was found") from err

        return cli_output(config_contents)

    def write_config(self, provisioner: str = ""):
        """Write config to file."""
        provisioner_plugin = self._select_provisioner(instance_id=provisioner).plugin
        # access private method for introspection
        # pylint: disable=protected-access
        provisioner_plugin._write_launchpad_file()

    def client_bundle(
        self, provisioner: str = "", user: str = "admin", reload: bool = False
    ):
        """Tell Launchpad to download the client bundle."""
        provisioner_plugin = self._select_provisioner(instance_id=provisioner)
        plugin = provisioner_plugin.plugin

        logger.info("Downloading client bungle for user: %s", user)
        try:
            # access private method for manual interaction
            # pylint: disable=protected-access
            bundle = plugin._mke_client_bundle(user=user, reload=reload)
        except Exception as err:
            raise Exception("Launchpad command failed.") from err

        return cli_output(bundle)

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
