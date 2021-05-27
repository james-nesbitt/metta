"""

Metta sonobuoy CLI plugin.

Provides functionality to manually run and inspect sonobuoy jobs

"""
import logging
import time

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.workload import METTA_PLUGIN_TYPE_WORKLOAD
from mirantis.testing.metta_cli.base import CliBase, cli_output

from .sonobuoy import METTA_PLUGIN_ID_SONOBUOY_WORKLOAD, Status

logger = logging.getLogger('metta.cli.sonobuoy')

METTA_PLUGIN_ID_SONOBUOY_CLI = 'metta_sonobuoy_cli'
""" cli plugin_id for the sonobuoy plugin """


# this interface is common for all Metta plugins, but CLI plugins underuse it
# pylint: disable=too-few-public-methods
class SonobuoyCliPlugin(CliBase):
    """Fire command/group generator for sonobuoy commands."""

    def fire(self):
        """Return CLI Command group."""
        if self.environment.fixtures.get(plugin_type=METTA_PLUGIN_TYPE_WORKLOAD,
                                         plugin_id=METTA_PLUGIN_ID_SONOBUOY_WORKLOAD,
                                         exception_if_missing=False) is not None:
            return {
                'contrib': {
                    'sonobuoy': SonobuoyGroup(self.environment)
                }
            }

        return {}


class SonobuoyGroup():
    """Base Fire command group for sonobuoy cli commands."""

    def __init__(self, environment: Environment):
        """Inject Environment into command group."""
        self.environment = environment

    def _select_fixture(self, instance_id: str = ''):
        """Pick a matching workload plugin."""
        try:
            if instance_id:
                return self.environment.fixtures.get(
                    plugin_type=METTA_PLUGIN_TYPE_WORKLOAD,
                    plugin_id=METTA_PLUGIN_ID_SONOBUOY_WORKLOAD, instance_id=instance_id)

            # Get the highest priority provisioner
            return self.environment.fixtures.get(
                plugin_type=METTA_PLUGIN_TYPE_WORKLOAD, plugin_id=METTA_PLUGIN_ID_SONOBUOY_WORKLOAD)

        except KeyError as err:
            raise ValueError("No usable kubernetes client was found for sonobuoy"
                             "to pull a kubeconfig from") from err

    def _select_instance(self, instance_id: str = ''):
        """Create a sonobuoy workload plugin instance."""
        fixture = self._select_fixture(instance_id=instance_id)
        plugin = fixture.plugin
        # @TODO allow filtering of kubernetes client instances
        instance = plugin.create_instance(self.environment.fixtures)
        return instance

    def info(self, instance_id: str = '', deep: bool = False):
        """Get info about a provisioner plugin."""
        fixture = self._select_fixture(instance_id=instance_id)

        info = {
            'fixture': {
                'plugin_type': fixture.plugin_type,
                'plugin_id': fixture.plugin_id,
                'instance_id': fixture.instance_id,
                'priority': fixture.priority,
            }
        }

        if deep:
            if hasattr(fixture.plugin, 'info'):
                info.update(fixture.plugin.info(True))

        return cli_output(info)

    def status(self, instance_id: str = ''):
        """Get active sonobuoy status."""
        instance = self._select_instance(instance_id=instance_id)
        status = instance.status()

        if status is None:
            status_info = {
                'status': "None",
                'plugins': {}
            }
        else:
            status_info = {
                'status': status.status.value,
                'plugins': {plugin_id: status.plugin(plugin_id) for
                            plugin_id in status.plugin_list()}
            }

        return cli_output(status_info)

    # pylint: disable=protected-access
    def crb(self, instance_id: str = '', remove: bool = False):
        """Create the crb needed to run sonobuoy."""
        instance = self._select_instance(instance_id=instance_id)

        if remove:
            instance._delete_k8s_crb()
        else:
            instance._create_k8s_crb()

    def run(self, instance_id: str = '', wait: bool = False):
        """Run sonobuoy workload."""
        instance = self._select_instance(instance_id=instance_id)
        instance.apply(wait=wait)

    def wait(self, instance_id: str = '', step: int = 5, limit: int = 1000):
        """Wait until no longer running."""
        instance = self._select_instance(instance_id=instance_id)
        print('{')
        for i in range(0, limit):
            status = instance.status()
            if status is None:
                status_info = {
                    'status': "None",
                    'plugins': {}
                }
            else:
                status_info = {
                    'status': status.status.value,
                    'plugins': {plugin_id: status.plugin(plugin_id) for
                                plugin_id in status.plugin_list()}
                }

            print(f"{i}: {status_info},")
            if status is None or status.status not in [Status.RUNNING]:
                break

            time.sleep(step)
        print('}')

    def destroy(self, instance_id: str = '', wait: bool = False):
        """Remove all sonobuoy infrastructure."""
        instance = self._select_instance(instance_id=instance_id)
        instance.destroy(wait=wait)

    def logs(self, instance_id: str = '', follow: bool = False):
        """Retrieve sonobuoy logs."""
        instance = self._select_instance(instance_id=instance_id)
        instance.logs(follow=follow)

    def retrieve(self, instance_id: str = ''):
        """Retrieve the results from the sonobuoy workload instance."""
        instance = self._select_instance(instance_id=instance_id)
        try:
            instance.retrieve()

        # broad catch to allow message formatting for cli output
        # pylint: disable=broad-except
        except Exception as err:
            logger.error("Retrieve failed: %s", err)
