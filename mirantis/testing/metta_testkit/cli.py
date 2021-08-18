"""

Metta cli plugin for testkit.

Mainly provides functionality for interacting with the testkit provisioner.

"""
import logging

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta_cli.base import CliBase, cli_output

from .provisioner import METTA_TESTKIT_PROVISIONER_PLUGIN_ID
from .client import METTA_TESTKIT_CLIENT_PLUGIN_ID

logger = logging.getLogger("metta.cli.testkit")

METTA_TESTKIT_CLI_PLUGIN_ID = "metta_testkit_cli"
""" metta plugin id for the testkit cli plugin """


# this interface is common for all Metta plugins, but CLI plugins underuse it
# pylint: disable=too-few-public-methods
class TestkitCliPlugin(CliBase):
    """Fire command/group generator for testkit commands."""

    def fire(self):
        """Return a dict of commands."""
        commands = {}

        if (
            self._environment.fixtures().get(
                plugin_id=METTA_TESTKIT_CLIENT_PLUGIN_ID,
                exception_if_missing=False,
            )
            is not None
        ):
            commands["testkit"] = TestkitClientGroup(self._environment)

        return commands


class TestkitClientGroup:
    """Testkit client commands."""

    def __init__(self, environment: Environment):
        """Inject environment."""
        self._environment: Environment = environment

        if (
            self._environment.fixtures().get(
                plugin_id=METTA_TESTKIT_PROVISIONER_PLUGIN_ID,
                exception_if_missing=False,
            )
            is not None
        ):
            self.provisioner = TestkitProvisionerGroup(self._environment)

    def _select_client(self, instance_id: str = ""):
        """Pick a matching client."""
        if instance_id:
            return self._environment.fixtures().get(
                plugin_id=METTA_TESTKIT_CLIENT_PLUGIN_ID,
                instance_id=instance_id,
            )

        # Get the highest priority provisioner
        return self._environment.fixtures().get(
            plugin_id=METTA_TESTKIT_CLIENT_PLUGIN_ID,
        )

    def info(self, client: str = "", deep: bool = False):
        """Get info about a client plugin."""
        fixture = self._select_client(instance_id=client)
        return cli_output(fixture.info(deep=deep))

    def create(self, client: str = ""):
        """Run  testkit create."""
        client_plugin = self._select_client(instance_id=client).plugin
        return cli_output(client_plugin.create())

    def destroy(self, client: str = ""):
        """Run testkit system rm."""
        client_plugin = self._select_client(instance_id=client).plugin
        return cli_output(client_plugin.destroy())

    def systems(self, client: str = ""):
        """List the systems that testkit is aware of."""
        client_plugin = self._select_client(instance_id=client).plugin
        return cli_output(client_plugin.system_ls())

    def machines(self, client: str = ""):
        """List the systems that testkit is aware of."""
        client_plugin = self._select_client(instance_id=client).plugin
        return cli_output(client_plugin.machine_ls())

    def exec(self, host: str, cmd: str, client: str = ""):
        """List the systems that testkit is aware of."""
        client_plugin = self._select_client(instance_id=client).plugin
        client_plugin.exec(host=host, cmd=cmd)


class TestkitProvisionerGroup:
    """Base Fire command group for testkit provisioner commands."""

    def __init__(self, environment: Environment):
        """Inject environment."""
        self._environment: Environment = environment

    def _select_provisioner(self, instance_id: str = ""):
        """Pick a matching provisioner."""
        if instance_id:
            return self._environment.fixtures().get(
                plugin_id=METTA_TESTKIT_PROVISIONER_PLUGIN_ID,
                instance_id=instance_id,
            )

        # Get the highest priority provisioner
        return self._environment.fixtures().get(
            plugin_id=METTA_TESTKIT_PROVISIONER_PLUGIN_ID,
        )

    def info(self, provisioner: str = "", deep: bool = False):
        """Get info about a provisioner plugin."""
        fixture = self._select_provisioner(instance_id=provisioner)
        return cli_output(fixture.info(deep=deep))

    def prepare(self, provisioner: str = ""):
        """Run the provisioner prepare : which for testkit currently does nothing."""
        provisioner_plugin = self._select_provisioner(instance_id=provisioner).plugin
        return cli_output(provisioner_plugin.prepare())

    def apply(self, provisioner: str = ""):
        """Run the provisioner apply, which runs testkit create."""
        provisioner_plugin = self._select_provisioner(instance_id=provisioner).plugin
        return cli_output(provisioner_plugin.apply())

    def destroy(self, provisioner: str = ""):
        """Run the provisioner destroy, which runs testkit system rm."""
        provisioner_plugin = self._select_provisioner(instance_id=provisioner).plugin
        return cli_output(provisioner_plugin.destroy())
