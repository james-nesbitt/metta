"""

Metta cli plugin for testkit.

Mainly provides functionality for interacting with the testkit provisioner.

"""
import logging


from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.provisioner import METTA_PLUGIN_TYPE_PROVISIONER
from mirantis.testing.metta_cli.base import CliBase, cli_output

logger = logging.getLogger('metta.cli.testkit')

METTA_PLUGIN_ID_TESTKIT_CLI = 'metta_testkit'
""" metta plugin id for the testkit cli plugin """


# this interface is common for all Metta plugins, but CLI plugins underuse it
# pylint: disable=too-few-public-methods
class TestkitCliPlugin(CliBase):
    """Fire command/group generator for testkit commands."""

    def fire(self):
        """Return a dict of commands."""
        if self.environment.fixtures.get(
                plugin_type=METTA_PLUGIN_TYPE_PROVISIONER, plugin_id=METTA_PLUGIN_ID_TESTKIT_CLI,
                exception_if_missing=False) is not None:
            return {
                'contrib': {
                    'testkit': TestkitGroup(self.environment)
                }
            }

        return {}


class TestkitGroup():
    """Base Fire command group for testkit commands."""

    def __init__(self, environment: Environment):
        """Inject environment."""
        self.environment = environment

    def _select_provisioner(self, instance_id: str = ''):
        """Pick a matching provisioner."""
        if instance_id:
            return self.environment.fixtures.get(
                plugin_type=METTA_PLUGIN_TYPE_PROVISIONER, plugin_id=METTA_PLUGIN_ID_TESTKIT_CLI,
                instance_id=instance_id)

        # Get the highest priority provisioner
        return self.environment.fixtures.get(
            plugin_type=METTA_PLUGIN_TYPE_PROVISIONER, plugin_id=METTA_PLUGIN_ID_TESTKIT_CLI)

    def info(self, provisioner: str = '', deep: bool = False):
        """Get info about a provisioner plugin."""
        fixture = self._select_provisioner(instance_id=provisioner)

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

    def prepare(self, provisioner: str = ''):
        """Run the provisioner prepare : which for testkit currently does nothing."""

    def apply(self, provisioner: str = ''):
        """Run the provisioner apply, which runs testkit create."""
        plugin = self._select_provisioner(instance_id=provisioner).plugin
        return cli_output(plugin.apply())

    def destroy(self, provisioner: str = ''):
        """Run the provisioner destroy, which runs testkit system rm."""
        plugin = self._select_provisioner(instance_id=provisioner).plugin
        return cli_output(plugin.destroy())

    def system_ls(self, provisioner: str = ''):
        """List the systems that testkit is aware of."""
        plugin = self._select_provisioner(instance_id=provisioner).plugin
        testkit = plugin.testkit
        return cli_output(testkit.system_ls())

    def hosts(self, provisioner: str = ''):
        """List the systems that testkit is aware of."""
        plugin = self._select_provisioner(instance_id=provisioner).plugin
        testkit = plugin.testkit
        return cli_output(testkit.machine_ls(plugin.system_name))
