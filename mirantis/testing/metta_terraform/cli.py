"""

Metta terraform CLI plugin.

Provides functionality to inspect terraform configuration and execute
terraform operations, as well as check out terraform outputs.

"""
import logging
from typing import Dict, Any

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.provisioner import METTA_PLUGIN_TYPE_PROVISIONER
from mirantis.testing.metta_cli.base import CliBase, cli_output

from .provisioner import METTA_TERRAFORM_PROVISIONER_PLUGIN_ID

logger = logging.getLogger('metta.cli.terraform')

METTA_TERRAFORM_CLI_PLUGIN_ID = 'metta_terraform'
""" cli plugin_id for the info plugin """


# this interface is common for all Metta plugins, but CLI plugins underuse it
# pylint: disable=too-few-public-methods
class TerraformCliPlugin(CliBase):
    """Fire command/group generator for terraform commands."""

    def fire(self):
        """Return a dict of commands.

        Don't return any commands if there is no provisioner plugin available

        """
        if self.environment.fixtures.get(plugin_type=METTA_PLUGIN_TYPE_PROVISIONER,
                                         plugin_id=METTA_TERRAFORM_PROVISIONER_PLUGIN_ID,
                                         exception_if_missing=False) is not None:
            return {
                'contrib': {
                    'terraform': TerraformGroup(self.environment)
                }
            }

        return {}


class TerraformGroup():
    """Base Fire command group for terraform cli commands."""

    def __init__(self, environment: Environment):
        """Inject environment."""
        self.environment = environment

    def _select_provisioner(self, instance_id: str = ''):
        """Pick a matching terraform provisioner."""
        if instance_id:
            return self.environment.fixtures.get(
                plugin_type=METTA_PLUGIN_TYPE_PROVISIONER,
                plugin_id=METTA_TERRAFORM_PROVISIONER_PLUGIN_ID,
                instance_id=instance_id)

        # Get the highest priority provisioner
        return self.environment.fixtures.get(
            plugin_type=METTA_PLUGIN_TYPE_PROVISIONER,
            plugin_id=METTA_TERRAFORM_PROVISIONER_PLUGIN_ID)

    def info(self, provisioner: str = '', deep: bool = False) -> Dict[str, Any]:
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
                plugin_info = fixture.plugin.info()
                if isinstance(plugin_info, dict):
                    info.update(plugin_info)

            if hasattr(fixture.plugin, 'get_fixtures'):
                fixtures = {}
                for sub_fixture in fixture.plugin.get_fixtures().to_list():
                    fixture_info = {
                        'fixture': {
                            'plugin_type': sub_fixture.plugin_type,
                            'plugin_id': sub_fixture.plugin_id,
                            'instance_id': sub_fixture.instance_id,
                            'priority': sub_fixture.priority,
                        }
                    }
                    if hasattr(sub_fixture.plugin, 'info'):
                        plugin_info = sub_fixture.plugin.info()
                        if isinstance(plugin_info, dict):
                            fixture_info.update(plugin_info)
                    fixtures[sub_fixture.instance_id] = fixture_info
                info['fixtures'] = fixtures

        return cli_output(info)

    def fixtures(self, provisioner: str = ''):
        """List all fixtures for this provisioner."""
        provisioner_plugin = self._select_provisioner(instance_id=provisioner).plugin
        fixture_list = [{
            'plugin_type': fixture.plugin_type,
            'plugin_id': fixture.plugin_id,
            'instance_id': fixture.instance_id,
            'priority': fixture.priority,
        } for fixture in provisioner_plugin.fixtures]

        cli_output(fixture_list)

    def prepare(self, provisioner: str = ''):
        """Run provisioner prepare."""
        provisioner_plugin = self._select_provisioner(instance_id=provisioner).plugin
        provisioner_plugin.prepare()

    def apply(self, provisioner: str = ''):
        """Run provisioner apply."""
        provisioner_plugin = self._select_provisioner(instance_id=provisioner).plugin
        provisioner_plugin.apply()

    def check(self, provisioner: str = ''):
        """Run provisioner check."""
        provisioner_plugin = self._select_provisioner(instance_id=provisioner).plugin
        provisioner_plugin.check()

    def destroy(self, provisioner: str = ''):
        """Run provisioner destroy."""
        provisioner_plugin = self._select_provisioner(instance_id=provisioner).plugin
        provisioner_plugin.destroy()
