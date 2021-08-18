"""

Metta CLI : Provisioner commands.

Various commands that allow introspection of provisioner plugins/fixtures and
their contents.

"""
import logging


from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.provisioner import METTA_PLUGIN_INTERFACE_ROLE_PROVISIONER

from .base import CliBase, cli_output

logger = logging.getLogger("metta.cli.provisioner")


# this interface is common for all Metta plugins, but CLI plugins underuse it
# pylint: disable=too-few-public-methods
class ProvisionerCliPlugin(CliBase):
    """Fire command/group generator for provisioner commands."""

    def fire(self):
        """Return a dict of commands."""
        return {"provisioner": ProvisionerGroup(self._environment)}


class ProvisionerGroup:
    """Base Fire command group for provisioner commands."""

    def __init__(self, environment: Environment):
        """Create CLI command group."""
        self._environment: Environment = environment

    def list(self, raw: bool = False):
        """List all provisioners."""
        provisioner_list = [
            fixture.plugin.instance_id
            for fixture in self._environment.fixtures().filter(
                interfaces=[METTA_PLUGIN_INTERFACE_ROLE_PROVISIONER]
            )
        ]

        if raw:
            return list
        return cli_output(provisioner_list)

    def _select_provisioner(self, instance_id: str = ""):
        """Pick a matching provisioner."""
        if instance_id:
            return self._environment.fixtures().get(
                interfaces=[METTA_PLUGIN_INTERFACE_ROLE_PROVISIONER],
                instance_id=instance_id,
            )
        # Get the highest priority provisioner
        return self._environment.fixtures().get(
            interfaces=[METTA_PLUGIN_INTERFACE_ROLE_PROVISIONER]
        )

    def info(self, provisioner: str = "", deep: bool = True):
        """Get info about a provisioner plugin."""
        fixture = self._select_provisioner(instance_id=provisioner)
        return cli_output(fixture.info(deep=deep))

    def fixtures(self, provisioner: str = "", deep: bool = False):
        """List all fixtures for this provisioner."""
        provisioner_plugin = self._select_provisioner(instance_id=provisioner).plugin
        if not hasattr(provisioner_plugin, "fixtures"):
            raise ValueError("This provisioner does not keep fixtures.")

        return cli_output(provisioner_plugin.fixtures.info(deep=deep))

    # 'up' is a common handler for provisioning.
    # pylint: disable=invalid-name
    def up(self, provisioner: str = ""):
        """Prepare and apply a provisioner."""
        provisioner_plugin = self._select_provisioner(instance_id=provisioner).plugin
        provisioner_plugin.prepare()
        provisioner_plugin.apply()

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
