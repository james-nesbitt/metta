"""

Metta sonobuoy CLI plugin.

Provides functionality to manually run and inspect sonobuoy jobs

"""
import logging
import time
from typing import Dict, Any

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.fixture import Fixture
from mirantis.testing.metta_cli.base import CliBase, cli_output

from .client import METTA_SONOBUOY_CLIENT_PLUGIN_ID, SonobuoyClientPlugin
from .workload import METTA_SONOBUOY_WORKLOAD_PLUGIN_ID
from .results import Status

logger = logging.getLogger("metta.cli.sonobuoy")

METTA_PLUGIN_ID_SONOBUOY_CLI = "metta_sonobuoy_cli"
""" cli plugin_id for the sonobuoy plugin """


# this interface is common for all Metta plugins, but CLI plugins underuse it
# pylint: disable=too-few-public-methods
class SonobuoyCliPlugin(CliBase):
    """Fire command/group generator for sonobuoy commands."""

    def fire(self):
        """Return CLI Command group."""
        commands: Dict[str, Any] = {}

        if (
            self._environment.fixtures().get(
                plugin_id=METTA_SONOBUOY_CLIENT_PLUGIN_ID,
                exception_if_missing=False,
            )
            is not None
        ):
            commands["sonobuoy"] = SonobuoyClientGroup(self._environment)

        return commands


class SonobuoyClientGroup:
    """Sonobuoy cli commands."""

    def __init__(self, environment: Environment):
        """Inject Environment into command group."""
        self._environment: Environment = environment

        if (
            self._environment.fixtures().get(
                plugin_id=METTA_SONOBUOY_WORKLOAD_PLUGIN_ID,
                exception_if_missing=False,
            )
            is not None
        ):
            self.workload = SonobuoyWorkloadGroup(self._environment)

    def _select_fixture(self, instance_id: str = "") -> Fixture:
        """Pick a matching client plugin."""
        try:
            if instance_id:
                return self._environment.fixtures().get(
                    plugin_id=METTA_SONOBUOY_CLIENT_PLUGIN_ID,
                    instance_id=instance_id,
                )

            # Get the highest priority provisioner
            return self._environment.fixtures().get(
                plugin_id=METTA_SONOBUOY_CLIENT_PLUGIN_ID,
            )

        except KeyError as err:
            raise ValueError("No usable sonobuoy client was found.") from err

    def info(self, instance_id: str = "", deep: bool = False):
        """Get info about a sonobuoy plugin."""
        fixture = self._select_fixture(instance_id=instance_id)
        return cli_output(fixture.info(deep=deep))

    def status(self, instance_id: str = ""):
        """Get active sonobuoy status."""
        client_plugin = self._select_fixture(instance_id=instance_id).plugin
        status = client_plugin.status()

        if status is None:
            status_info = {"status": "None", "plugins": {}}
        else:
            status_info = {
                "status": status.status,
                "plugins": {
                    plugin_id: status.plugin(plugin_id) for plugin_id in status.plugin_list()
                },
            }

        return cli_output(status_info)

    # pylint: disable=protected-access
    def crb(self, instance_id: str = "", remove: bool = False):
        """Create the crb needed to run sonobuoy."""
        client_plugin = self._select_fixture(instance_id=instance_id).plugin

        if remove:
            client_plugin._sonobuoy._delete_k8s_crb()
        else:
            client_plugin._sonobuoy._create_k8s_crb()

    def run(self, instance_id: str = "", wait: bool = False):
        """Run sonobuoy."""
        client_plugin = self._select_fixture(instance_id=instance_id).plugin
        client_plugin.run(wait=wait)

    def wait(self, instance_id: str = "", step: int = 5, limit: int = 1000):
        """Wait until no longer running."""
        client_plugin = self._select_fixture(instance_id=instance_id).plugin
        print("{")
        for i in range(0, limit):
            status = client_plugin.status()
            if status is None:
                status_info = {"status": "None", "plugins": {}}
            else:
                status_info = {
                    "status": status.status.value,
                    "plugins": {
                        plugin_id: status.plugin(plugin_id) for plugin_id in status.plugin_list()
                    },
                }

            print(f"{i}: {status_info},")
            if status is None or status.status not in [Status.RUNNING]:
                break

            time.sleep(step)
        print("}")

    def delete(self, instance_id: str = "", wait: bool = False):
        """Remove all sonobuoy infrastructure."""
        client_plugin = self._select_fixture(instance_id=instance_id).plugin
        client_plugin.delete(wait=wait)

    def logs(self, instance_id: str = "", follow: bool = False):
        """Retrieve sonobuoy logs."""
        client_plugin = self._select_fixture(instance_id=instance_id).plugin
        client_plugin.logs(follow=follow)

    def results(self, instance_id: str = ""):
        """Retrieve sonobuoy results."""
        client_plugin = self._select_fixture(instance_id=instance_id).plugin
        results: str = client_plugin.results()
        return results

    def retrieve(self, instance_id: str = ""):
        """Retrieve the results from the sonobuoy workload instance."""
        client_plugin = self._select_fixture(instance_id=instance_id).plugin

        try:
            client_plugin.retrieve()
        # broad catch to allow message formatting for cli output
        # pylint: disable=broad-except
        except Exception as err:
            logger.error("Retrieve failed: %s", err)

    def version(self, instance_id: str = ""):
        """Retrieve the sonobuoy version string."""
        client_plugin = self._select_fixture(instance_id=instance_id).plugin
        return cli_output(client_plugin.version())

    def health(self, instance_id: str = ""):
        """Retrieve the results from the sonobuoy workload instance."""
        client_plugin = self._select_fixture(instance_id=instance_id).plugin
        health = client_plugin.health()

        return cli_output(
            {
                "status": health.status(),
                "messages": list(health.messages()),
            }
        )

    def create_k8s_crb(self, instance_id: str = ""):
        """Create the cluster role binding that sonobuoy needs."""
        client_plugin = self._select_fixture(instance_id=instance_id).plugin
        return cli_output(client_plugin._sonobuoy.create_k8s_crb())

    def delete_k8s_crb(self, instance_id: str = ""):
        """Remove the cluster role binding that we created."""
        client_plugin = self._select_fixture(instance_id=instance_id).plugin
        return cli_output(client_plugin._sonobuoy.delete_k8s_crb())


class SonobuoyWorkloadGroup:
    """Sonobuoy workload commands."""

    def __init__(self, environment: Environment):
        """Inject Environment into command group."""
        self._environment: Environment = environment

    def _select_fixture(self, instance_id: str = "") -> Fixture:
        """Pick a matching workload plugin."""
        try:
            if instance_id:
                return self._environment.fixtures().get(
                    plugin_id=METTA_SONOBUOY_WORKLOAD_PLUGIN_ID,
                    instance_id=instance_id,
                )

            # Get the highest priority provisioner
            return self._environment.fixtures().get(
                plugin_id=METTA_SONOBUOY_WORKLOAD_PLUGIN_ID,
            )

        except KeyError as err:
            raise ValueError("No usable sonobuoy client was found.") from err

    def _prepared_fixture(self, instance_id: str = "") -> Fixture:
        """Pick a matching workload plugin and prepare it."""
        sonobuoy_fixture: Fixture = self._select_fixture(instance_id=instance_id)
        sonobuoy_fixture.plugin.prepare()
        return sonobuoy_fixture

    def _client_plugin(self, instance_id: str = "") -> SonobuoyClientPlugin:
        """Get the workload's client plugin."""
        return self._prepared_fixture(instance_id=instance_id).plugin.get_client_plugin()

    def info(self, instance_id: str = "", deep: bool = False):
        """Get info about a sonobuoy plugin."""
        fixture = self._select_fixture(instance_id=instance_id)
        return cli_output(fixture.info(deep=deep))

    def apply(self, instance_id: str = "", wait: bool = False):
        """Run sonobuoy."""
        workload_plugin = self._select_fixture(instance_id=instance_id).plugin
        workload_plugin.apply(wait=wait)

    def destroy(self, instance_id: str = "", wait: bool = False):
        """Remove all sonobuoy infrastructure."""
        workload_plugin = self._select_fixture(instance_id=instance_id).plugin
        workload_plugin.destroy(wait=wait)

    def logs(self, instance_id: str = "", follow: bool = False):
        """Retrieve sonobuoy logs."""
        client_plugin = self._client_plugin(instance_id=instance_id)
        client_plugin.logs(follow=follow)

    def retrieve(self, instance_id: str = ""):
        """Retrieve the results from the sonobuoy workload instance."""
        client_plugin = self._client_plugin(instance_id=instance_id)

        try:
            client_plugin.retrieve()
        # broad catch to allow message formatting for cli output
        # pylint: disable=broad-except
        except Exception as err:
            logger.error("Retrieve failed: %s", err)
