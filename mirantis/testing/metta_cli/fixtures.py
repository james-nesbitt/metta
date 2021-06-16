"""

Metta CLI : Fixture commands.

Cli plugin that allows examination of fixtures in environments.

"""

import logging

from mirantis.testing.metta.plugin import Factory
from mirantis.testing.metta.environment import Environment

from .base import CliBase, cli_output

logger = logging.getLogger('metta.cli.fixtures')


# this interface is common for all Metta plugins, but CLI plugins underuse it
# pylint: disable=too-few-public-methods
class FixturesCliPlugin(CliBase):
    """Fire command/group generator for fixture commands."""

    def fire(self):
        """Return a dict of commands."""
        return {
            'fixture': FixturesGroup(self.environment)
        }


class FixturesGroup():
    """Base Fire command group for fixtures commands."""

    def __init__(self, environment: Environment):
        """Attach environment to object."""
        self._environment = environment

    def list(self, plugin_type: str = '', plugin_id: str = '', instance_id: str = ''):
        """Return List all fixture instance_ids."""
        fixture_list = []
        for fixture in self._environment.fixtures.filter(plugin_type=plugin_type,
                                                         plugin_id=plugin_id,
                                                         instance_id=instance_id):

            fixture_list.append(fixture.instance_id)

        return cli_output(fixture_list)

    # needs to be a method for registration in fire
    # pylint: disable=no-self-use
    def plugin_types(self):
        """List plugins that have been registered with the environment."""
        plugin_list = {}
        for plugin_type in Factory.plugin_types():
            plugin_list[plugin_type] = []
            for plugin_id in Factory.plugins(plugin_type):
                plugin_list[plugin_type].append(plugin_id)

        return cli_output(plugin_list)

    def info(self, deep: bool = False, plugin_type: str = '', plugin_id: str = '',
             instance_id: str = ''):
        """Return Info for fixtures."""
        fixture_info_list = []
        for fixture in self._environment.fixtures.filter(
                plugin_type=plugin_type, plugin_id=plugin_id, instance_id=instance_id):

            info = {
                'fixture': {
                    'plugin_type': fixture.plugin_type,
                    'plugin_id': fixture.plugin_id,
                    'instance_id': fixture.instance_id,
                    'priority': fixture.priority,
                }
            }

            if deep and hasattr(fixture.plugin, 'info'):
                plugin_info = fixture.plugin.info()
                if isinstance(plugin_info, dict):
                    info.update(plugin_info)

            fixture_info_list.append(info)

        return cli_output(fixture_info_list)
