"""

Metta litmus chaos CLI plugin.

Provides functionality to manually run and inspect litmus chaos jobs

"""
import logging

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.workload import METTA_PLUGIN_INTERFACE_ROLE_WORKLOAD
from mirantis.testing.metta_cli.base import CliBase, cli_output

from .litmuschaos_workload import METTA_PLUGIN_ID_LITMUSCHAOS_WORKLOAD

logger = logging.getLogger("metta_litmuschaos.cli")

METTA_PLUGIN_ID_LITMUSCHAOS_CLI = "metta_litmuschaos_cli"
""" cli plugin_id for the litmuschaos plugin """


# this interface is common for all Metta plugins, but CLI plugins underuse it
# pylint: disable=too-few-public-methods
class LitmusChaosCliPlugin(CliBase):
    """Fire command/group generator for litmus-chaos commands."""

    def fire(self):
        """Return a dict of commands for litmuschaos workloads."""
        if (
            self.environment.fixtures().get(
                plugin_type=METTA_PLUGIN_INTERFACE_ROLE_WORKLOAD,
                plugin_id=METTA_PLUGIN_ID_LITMUSCHAOS_WORKLOAD,
                exception_if_missing=False,
            )
            is not None
        ):
            return {"contrib": {"litmuschaos": LitmusChaosGroup(self.environment)}}

        return {}


class LitmusChaosGroup:
    """Base Fire command group for litmus-chaos cli commands."""

    def __init__(self, environment: Environment):
        """Configure command group."""
        self.environment = environment

    def _select_fixture(self, instance_id: str = ""):
        """Pick a matching workload plugin."""
        try:
            if instance_id:
                return self.environment.fixtures().get(
                    plugin_type=METTA_PLUGIN_INTERFACE_ROLE_WORKLOAD,
                    plugin_id=METTA_PLUGIN_ID_LITMUSCHAOS_WORKLOAD,
                    instance_id=instance_id,
                )

            # Get the highest priority provisioner
            return self.environment.fixtures().get(
                plugin_type=METTA_PLUGIN_INTERFACE_ROLE_WORKLOAD,
                plugin_id=METTA_PLUGIN_ID_LITMUSCHAOS_WORKLOAD,
            )

        except KeyError as err:
            raise ValueError(
                "No usable kubernetes client was found for litmuschaos to "
                "pull a kubeconfig from"
            ) from err

    def _select_instance(self, instance_id: str = ""):
        """Create a litmuschaos workload plugin instance."""
        fixture = self._select_fixture(instance_id=instance_id)
        plugin = fixture.plugin
        # @TODO allow filtering of kubernetes client instances
        instance = plugin.create_instance(self.environment.fixtures())
        return instance

    def info(self, instance_id: str = "", deep: bool = False):
        """Get info about the plugin."""
        fixture = self._select_fixture(instance_id=instance_id)

        info = {
            "fixture": {
                "plugin_type": fixture.plugin_type,
                "plugin_id": fixture.plugin_id,
                "instance_id": fixture.instance_id,
                "priority": fixture.priority,
            },
        }

        if deep:
            if hasattr(fixture.plugin, "info"):
                info.update(fixture.plugin.info(True))

            instance = self._select_instance(instance_id=instance_id)
            info["instance"] = instance.info()

        return cli_output(info)

    def prepare(self, instance_id: str = ""):
        """Prepare the workload instance for running."""
        instance = self._select_instance(instance_id=instance_id)

        instance.prepare()
