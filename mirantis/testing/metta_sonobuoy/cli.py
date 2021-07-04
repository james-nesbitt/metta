"""

Metta sonobuoy CLI plugin.

Provides functionality to manually run and inspect sonobuoy jobs

"""
import logging
import time

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta_cli.base import CliBase, cli_output

from .sonobuoy_workload import METTA_PLUGIN_ID_SONOBUOY_WORKLOAD
from .sonobuoy import Status

logger = logging.getLogger("metta.cli.sonobuoy")

METTA_PLUGIN_ID_SONOBUOY_CLI = "metta_sonobuoy_cli"
""" cli plugin_id for the sonobuoy plugin """


# this interface is common for all Metta plugins, but CLI plugins underuse it
# pylint: disable=too-few-public-methods
class SonobuoyCliPlugin(CliBase):
    """Fire command/group generator for sonobuoy commands."""

    def fire(self):
        """Return CLI Command group."""
        if (
            self._environment.fixtures.get(
                plugin_id=METTA_PLUGIN_ID_SONOBUOY_WORKLOAD,
                exception_if_missing=False,
            )
            is not None
        ):
            return {"contrib": {"sonobuoy": SonobuoyGroup(self._environment)}}

        return {}


class SonobuoyGroup:
    """Base Fire command group for sonobuoy cli commands."""

    def __init__(self, environment: Environment):
        """Inject Environment into command group."""
        self._environment = environment

    def _select_fixture(self, instance_id: str = ""):
        """Pick a matching workload plugin."""
        try:
            if instance_id:
                return self._environment.fixtures.get(
                    plugin_id=METTA_PLUGIN_ID_SONOBUOY_WORKLOAD,
                    instance_id=instance_id,
                )

            # Get the highest priority provisioner
            return self._environment.fixtures.get(
                plugin_id=METTA_PLUGIN_ID_SONOBUOY_WORKLOAD,
            )

        except KeyError as err:
            raise ValueError(
                "No usable kubernetes client was found for sonobuoy"
                "to pull a kubeconfig from"
            ) from err

    def _prepared_plugin(self, instance_id: str = ""):
        """Select and prepare a sonobuoy workload plugin."""
        fixture = self._select_fixture(instance_id=instance_id)
        plugin = fixture.plugin
        plugin.prepare(self._environment.fixtures)
        return plugin

    def info(self, instance_id: str = "", deep: bool = False):
        """Get info about a sonobuoy plugin."""
        fixture = self._select_fixture(instance_id=instance_id)
        fixture.plugin.prepare(self._environment.fixtures)

        return cli_output(fixture.info(deep=deep))

    def status(self, instance_id: str = ""):
        """Get active sonobuoy status."""
        instance = self._prepared_plugin(instance_id=instance_id)
        status = instance.status()

        if status is None:
            status_info = {"status": "None", "plugins": {}}
        else:
            status_info = {
                "status": status.status,
                "plugins": {
                    plugin_id: status.plugin(plugin_id)
                    for plugin_id in status.plugin_list()
                },
            }

        return cli_output(status_info)

    # pylint: disable=protected-access
    def crb(self, instance_id: str = "", remove: bool = False):
        """Create the crb needed to run sonobuoy."""
        workload_plugin = self._prepared_plugin(instance_id=instance_id)

        if remove:
            workload_plugin._sonobuoy._delete_k8s_crb()
        else:
            workload_plugin._sonobuoy._create_k8s_crb()

    def run(self, instance_id: str = "", wait: bool = False):
        """Run sonobuoy workload."""
        workload_plugin = self._prepared_plugin(instance_id=instance_id)
        workload_plugin.apply(wait=wait)

    def wait(self, instance_id: str = "", step: int = 5, limit: int = 1000):
        """Wait until no longer running."""
        workload_plugin = self._prepared_plugin(instance_id=instance_id)
        print("{")
        for i in range(0, limit):
            status = workload_plugin.status()
            if status is None:
                status_info = {"status": "None", "plugins": {}}
            else:
                status_info = {
                    "status": status.status.value,
                    "plugins": {
                        plugin_id: status.plugin(plugin_id)
                        for plugin_id in status.plugin_list()
                    },
                }

            print(f"{i}: {status_info},")
            if status is None or status.status not in [Status.RUNNING]:
                break

            time.sleep(step)
        print("}")

    def destroy(self, instance_id: str = "", wait: bool = False):
        """Remove all sonobuoy infrastructure."""
        workload_plugin = self._prepared_plugin(instance_id=instance_id)
        workload_plugin.destroy(wait=wait)

    def logs(self, instance_id: str = "", follow: bool = False):
        """Retrieve sonobuoy logs."""
        workload_plugin = self._prepared_plugin(instance_id=instance_id)
        workload_plugin.logs(follow=follow)

    def retrieve(self, instance_id: str = ""):
        """Retrieve the results from the sonobuoy workload instance."""
        workload_plugin = self._prepared_plugin(instance_id=instance_id)
        try:
            workload_plugin.retrieve()

        # broad catch to allow message formatting for cli output
        # pylint: disable=broad-except
        except Exception as err:
            logger.error("Retrieve failed: %s", err)
