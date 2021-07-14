"""

Metta terraform CLI plugin.

Provides functionality to inspect terraform configuration and execute
terraform operations, as well as check out terraform outputs.

"""
import logging
from typing import Dict, Any

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta_cli.base import CliBase, cli_output

from .provisioner import METTA_TERRAFORM_PROVISIONER_PLUGIN_ID

logger = logging.getLogger("metta.cli.terraform")

METTA_TERRAFORM_CLI_PLUGIN_ID = "metta_terraform_cli"
""" cli plugin_id for the info plugin """


# this interface is common for all Metta plugins, but CLI plugins underuse it
# pylint: disable=too-few-public-methods
class TerraformCliPlugin(CliBase):
    """Fire command/group generator for terraform commands."""

    def fire(self):
        """Return a dict of commands.

        Don't return any commands if there is no provisioner plugin available

        """
        if (
            self._environment.fixtures.get(
                plugin_id=METTA_TERRAFORM_PROVISIONER_PLUGIN_ID,
                exception_if_missing=False,
            )
            is not None
        ):
            return {"contrib": {"terraform": TerraformGroup(self._environment)}}

        return {}


class TerraformGroup:
    """Base Fire command group for terraform cli commands."""

    def __init__(self, environment: Environment):
        """Inject environment."""
        self._environment = environment

    def _select_provisioner(self, instance_id: str = ""):
        """Pick a matching terraform provisioner."""
        if instance_id:
            return self._environment.fixtures.get(
                plugin_id=METTA_TERRAFORM_PROVISIONER_PLUGIN_ID,
                instance_id=instance_id,
            )

        # Get the highest priority provisioner
        return self._environment.fixtures.get(
            plugin_id=METTA_TERRAFORM_PROVISIONER_PLUGIN_ID,
        )

    def info(self, provisioner: str = "", deep: bool = False) -> Dict[str, Any]:
        """Get info about a provisioner plugin."""
        fixture = self._select_provisioner(instance_id=provisioner)
        return cli_output(fixture.info(deep=deep))

    def fixtures(self, provisioner: str = ""):
        """List all fixtures for this provisioner."""
        provisioner_plugin = self._select_provisioner(instance_id=provisioner).plugin
        fixture_list = [
            {
                "plugin_id": fixture.plugin_id,
                "instance_id": fixture.instance_id,
                "interfaces": fixture.interfaces,
                "priority": fixture.priority,
            }
            for fixture in provisioner_plugin.fixtures
        ]

        cli_output(fixture_list)

    def prepare(self, provisioner: str = ""):
        """Run provisioner prepare."""
        provisioner_plugin = self._select_provisioner(instance_id=provisioner).plugin
        provisioner_plugin.prepare()

    def apply(self, provisioner: str = ""):
        """Run provisioner apply."""
        provisioner_plugin = self._select_provisioner(instance_id=provisioner).plugin
        provisioner_plugin.apply()

    def check(self, provisioner: str = ""):
        """Run provisioner check."""
        provisioner_plugin = self._select_provisioner(instance_id=provisioner).plugin
        provisioner_plugin.check()

    def destroy(self, provisioner: str = ""):
        """Run provisioner destroy."""
        provisioner_plugin = self._select_provisioner(instance_id=provisioner).plugin
        provisioner_plugin.destroy()
