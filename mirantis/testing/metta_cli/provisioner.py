"""

Metta CLI : Provisioner commands.

Various commands that allow introspection of provisioner plugins/fixtures and
their contents.

"""
import logging


from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.provisioner import METTA_PLUGIN_TYPE_PROVISIONER

from .base import CliBase, cli_output

logger = logging.getLogger('metta.cli.provisioner')


# this interface is common for all Metta plugins, but CLI plugins underuse it
# pylint: disable=too-few-public-methods
class ProvisionerCliPlugin(CliBase):
    """Fire command/group generator for provisioner commands."""

    def fire(self):
        """Return a dict of commands."""
        return {
            'provisioner': ProvisionerGroup(self.environment)
        }


class ProvisionerGroup():
    """Base Fire command group for provisioner commands."""

    def __init__(self, environment: Environment):
        """Create CLI command group."""
        self.environment = environment

    def list(self, raw: bool = False):
        """List all provisioners."""
        provisioner_list = [
            fixture.plugin.instance_id for fixture in self.environment.fixtures.filter(
                plugin_type=METTA_PLUGIN_TYPE_PROVISIONER)]

        if raw:
            return list
        return cli_output(provisioner_list)

    def _select_provisioner(self, instance_id: str = ''):
        """Pick a matching provisioner."""
        if instance_id:
            return self.environment.fixtures.get(plugin_type=METTA_PLUGIN_TYPE_PROVISIONER,
                                                 instance_id=instance_id)
        # Get the highest priority provisioner
        return self.environment.fixtures.get(plugin_type=METTA_PLUGIN_TYPE_PROVISIONER)

    def info(self, provisioner: str = '', deep: bool = True):
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

    def fixtures(self, provisioner: str = '', deep: bool = False):
        """List all fixtures for this provisioner."""
        provisioner_plugin = self._select_provisioner(instance_id=provisioner).plugin
        if not hasattr(provisioner_plugin, 'get_fixtures'):
            raise ValueError('This provisioner does not keep fixtures.')

        fixture_list = {}
        for fixture in provisioner_plugin.get_fixtures():

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
                    info.update(fixture.plugin.info())

                if hasattr(fixture.plugin, 'get_fixtures'):
                    fixtures = {}
                    for sub_fixture in fixture.plugin.get_fixtures():
                        fixture_info = {
                            'fixture': {
                                'plugin_type': sub_fixture.plugin_type,
                                'plugin_id': sub_fixture.plugin_id,
                                'instance_id': sub_fixture.instance_id,
                                'priority': sub_fixture.priority,
                            }
                        }
                        if hasattr(sub_fixture.plugin, 'info'):
                            fixture_info.update(sub_fixture.plugin.info())

                        fixtures[sub_fixture.instance_id] = fixture_info

                    info['fixtures'] = fixtures

            fixture_list[fixture.instance_id] = info

        return cli_output(fixture_list)

    # 'up' is a common handler for provisioning.
    # pylint: disable=invalid-name
    def up(self, provisioner: str = ''):
        """Prepare and apply a provisioner."""
        provisioner_plugin = self._select_provisioner(instance_id=provisioner).plugin
        provisioner_plugin.prepare()
        provisioner_plugin.apply()

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
