"""

Metta cli plugin for interacting with configured k0s resources.

"""
import logging
from typing import Dict, Any

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta_cli.base import CliBase, cli_output

from .k0sctl_client import K0sctlClientPlugin, METTA_K0S_K0SCTL_CLIENT_PLUGIN_ID

logger = logging.getLogger("metta.cli.terraform")

METTA_K0S_CLI_PLUGIN_ID = "metta_terraform_cli"
""" cli plugin_id for the info plugin """


# this interface is common for all Metta plugins, but CLI plugins underuse it
# pylint: disable=too-few-public-methods
class K0sCliPlugin(CliBase):
    """Fire command/group generator for k0s commands."""

    def fire(self):
        """Return a dict of commands.

        Don't return any commands if there are no plugins available

        """
        commands: Dict[str, object] = {}

        if (
            self._environment.fixtures().get(
                plugin_id=METTA_K0S_K0SCTL_CLIENT_PLUGIN_ID,
                exception_if_missing=False,
            )
            is not None
        ):
            commands["k0sctl"] = K0sctlClientGroup(self._environment)

        return commands


class K0sctlClientGroup:
    """K0sCTL client cli commands."""

    def __init__(self, environment: Environment):
        """Inject environment."""
        self._environment: Environment = environment

    def _select_client(self, instance_id: str = "") -> K0sctlClientPlugin:
        """Pick a matching k0sctl client."""
        if instance_id:
            return self._environment.fixtures().get(
                plugin_id=METTA_K0S_CLI_PLUGIN_ID,
                instance_id=instance_id,
            )

        # Get the highest priority provisioner
        return self._environment.fixtures().get(
            plugin_id=METTA_K0S_K0SCTL_CLIENT_PLUGIN_ID,
        )

    def info(self, client: str = "", deep: bool = False) -> Dict[str, Any]:
        """Get info about a client plugin."""
        fixture = self._select_client(instance_id=client)
        return cli_output(fixture.info(deep=deep))
