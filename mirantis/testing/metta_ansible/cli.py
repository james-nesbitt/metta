"""

Metta CLI : Ansible Provisioner commands.

Comamnds for itneracting with the ansible plugins, primarily the provisioner

"""
import logging

from mirantis.testing.metta.environment import Environment

from mirantis.testing.metta_cli.base import CliBase, cli_output
from mirantis.testing.metta.provisioner import METTA_PLUGIN_TYPE_PROVISIONER

from .provisioner import METTA_ANSIBLE_PROVISIONER_PLUGIN_ID

logger = logging.getLogger('metta.cli.ansible')

METTA_ANSIBLE_CLI_PLUGIN_ID = 'metta_ansible'
""" cli plugin_id for the info plugin """


# this interface is common for all Metta plugins, but CLI plugins underuse it
# pylint: disable=too-few-public-methods
class AnsibleCliPlugin(CliBase):
    """Fire command/group generator for Ansible commands."""

    def fire(self):
        """Return a dict of commands."""
        if self.environment.fixtures.get(
                plugin_type=METTA_PLUGIN_TYPE_PROVISIONER,
                plugin_id=METTA_ANSIBLE_PROVISIONER_PLUGIN_ID,
                exception_if_missing=False) is not None:
            return {
                'contrib': {
                    'ansible': AnsibleGroup(self.environment)
                }
            }

        return {}


class AnsibleGroup():
    """Base Fire command group for Ansible commands."""

    def __init__(self, environment: Environment):
        """Inject environment into command gorup."""
        self.environment = environment

    def _select_provisioner(self, instance_id: str = ''):
        """Pick a matching provisioner."""
        if instance_id:
            return self.environment.fixtures.get(
                plugin_type=METTA_PLUGIN_TYPE_PROVISIONER,
                plugin_id=METTA_ANSIBLE_CLI_PLUGIN_ID, instance_id=instance_id)

        # Get the highest priority provisioner
        return self.environment.fixtures.get(
            plugin_type=METTA_PLUGIN_TYPE_PROVISIONER, plugin_id=METTA_ANSIBLE_CLI_PLUGIN_ID)

    def info(self, provisioner: str = ''):
        """Get info about a provisioner plugin."""
        fixture = self._select_provisioner(instance_id=provisioner)
        plugin = fixture.plugin

        info = {
            'fixture': {
                'plugin_type': fixture.plugin_type,
                'plugin_id': fixture.plugin_id,
                'instance_id': fixture.instance_id,
                'priority': fixture.priority
            }
        }
        info.update(plugin.info())

        return cli_output(info)

    def prepare(self, provisioner: str = ''):
        """Run provisioner prepare."""
        provisioner_plugin = self._select_provisioner(instance_id=provisioner).plugin
        provisioner_plugin.prepare()

    def apply(self, provisioner: str = ''):
        """Run provisioner apply."""
        provisioner_plugin = self._select_provisioner(instance_id=provisioner).plugin
        provisioner_plugin.apply()

    def destroy(self, provisioner: str = ''):
        """Run provisioner destroy."""
        provisioner_plugin = self._select_provisioner(instance_id=provisioner).plugin
        provisioner_plugin.destroy()
