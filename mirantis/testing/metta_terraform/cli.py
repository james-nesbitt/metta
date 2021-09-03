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
from .client import METTA_TERRAFORM_CLIENT_PLUGIN_ID

logger = logging.getLogger("metta.cli.terraform")

METTA_TERRAFORM_CLI_PLUGIN_ID = "metta_terraform_cli"
""" cli plugin_id for the info plugin """


# this interface is common for all Metta plugins, but CLI plugins underuse it
# pylint: disable=too-few-public-methods
class TerraformCliPlugin(CliBase):
    """Fire command/group generator for terraform commands."""

    def fire(self):
        """Return a dict of commands.

        Don't return any commands if there are no plugind available

        """
        commands: Dict[str, object] = {}

        if (
            self._environment.fixtures().get(
                plugin_id=METTA_TERRAFORM_CLIENT_PLUGIN_ID,
                exception_if_missing=False,
            )
            is not None
        ):
            commands["terraform"] = TerraformClientGroup(self._environment)

        return commands


class TerraformClientGroup:
    """Terraform client cli commands."""

    def __init__(self, environment: Environment):
        """Inject environment."""
        self._environment: Environment = environment

        if (
            self._environment.fixtures().get(
                plugin_id=METTA_TERRAFORM_PROVISIONER_PLUGIN_ID,
                exception_if_missing=False,
            )
            is not None
        ):
            self.provisioner = TerraformProvisionerGroup(self._environment)

    def _select_client(self, instance_id: str = ""):
        """Pick a matching terraform provisioner."""
        if instance_id:
            return self._environment.fixtures().get(
                plugin_id=METTA_TERRAFORM_CLIENT_PLUGIN_ID,
                instance_id=instance_id,
            )

        # Get the highest priority provisioner
        return self._environment.fixtures().get(
            plugin_id=METTA_TERRAFORM_CLIENT_PLUGIN_ID,
        )

    def info(self, client: str = "", deep: bool = False) -> Dict[str, Any]:
        """Get info about a client plugin."""
        fixture = self._select_client(instance_id=client)
        return cli_output(fixture.info(deep=deep))

    def init(self, client: str = ""):
        """Run terraform init."""
        plugin = self._select_client(instance_id=client).plugin
        plugin.init()

    def plan(self, client: str = ""):
        """Run client plan."""
        plugin = self._select_client(instance_id=client).plugin
        plugin.plan()

    def apply(self, client: str = "", nolock: bool = False):
        """Run terraform apply."""
        plugin = self._select_client(instance_id=client).plugin
        plugin.apply(lock=(not nolock))

    def destroy(self, client: str = "", nolock: bool = False):
        """Run terraform destroy."""
        plugin = self._select_client(instance_id=client).plugin
        plugin.destroy(lock=(not nolock))

    def check(self, client: str = ""):
        """Run client check."""
        plugin = self._select_client(instance_id=client).plugin
        plugin.check()

    def state(self, client: str = ""):
        """Run client check."""
        plugin = self._select_client(instance_id=client).plugin
        return cli_output(plugin.state())

    def output(self, client: str = "", name: str = ""):
        """Retrieve Terraform outputs."""
        plugin = self._select_client(instance_id=client).plugin
        return cli_output(plugin.output(name=name))


class TerraformProvisionerGroup:
    """Base Fire command group for terraform cli commands."""

    def __init__(self, environment: Environment):
        """Inject environment."""
        self._environment: Environment = environment

    def _select_provisioner(self, instance_id: str = ""):
        """Pick a matching terraform provisioner."""
        if instance_id:
            return self._environment.fixtures().get(
                plugin_id=METTA_TERRAFORM_PROVISIONER_PLUGIN_ID,
                instance_id=instance_id,
            )

        # Get the highest priority provisioner
        return self._environment.fixtures().get(
            plugin_id=METTA_TERRAFORM_PROVISIONER_PLUGIN_ID,
        )

    def info(self, provisioner: str = "", deep: bool = False) -> Dict[str, Any]:
        """Get info about a provisioner plugin."""
        fixture = self._select_provisioner(instance_id=provisioner)
        return cli_output(fixture.info(deep=deep))

    def prepare(self, provisioner: str = ""):
        """Run provisioner prepare."""
        plugin = self._select_provisioner(instance_id=provisioner).plugin
        plugin.prepare()

    def apply(self, provisioner: str = "", nolock: bool = False):
        """Run provisioner apply."""
        plugin = self._select_provisioner(instance_id=provisioner).plugin
        plugin.apply(lock=(not nolock))

    def destroy(self, provisioner: str = "", nolock: bool = False):
        """Run provisioner destroy."""
        plugin = self._select_provisioner(instance_id=provisioner).plugin
        plugin.destroy(lock=(not nolock))
