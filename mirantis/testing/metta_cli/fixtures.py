import logging
from typing import Dict, Any

import json

from mirantis.testing.metta.plugin import Type
from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.cli import CliBase

from .output import OutputGroup

logger = logging.getLogger('metta.cli.fixtures')


class FixturesCliPlugin(CliBase):

    def fire(self):
        """ return a dict of commands """
        return {
            'fixtures': FixturesGroup(self.environment)
        }


class FixturesGroup():

    def __init__(self, environment: Environment):
        self.environment = environment

    def list(self, include_cli_plugins: bool = False):
        """ List all fixture instance_ids """
        list = [fixture.instance_id for fixture in self.environment.fixtures.get_fixtures(
        ).to_list() if include_cli_plugins or fixture.type is not Type.CLI]

        return json.dumps(list, indent=2)

    def info(self, type: str = '', plugin_id: str = '',
             instance_id: str = '', deep: bool = False, include_cli_plugins: bool = False):
        """ Info for all fixtures """

        if type:
            type = Type.from_string(type)
        else:
            type = None

        list = []
        for fixture in self.environment.fixtures.get_fixtures(
                type=type, plugin_id=plugin_id, instance_id=instance_id).to_list():
            if not include_cli_plugins and fixture.type is Type.CLI:
                continue

            info = {
                'fixture': {
                    'type': fixture.type.value,
                    'plugin_id': fixture.plugin_id,
                    'instance_id': fixture.instance_id,
                    'priority': fixture.priority,
                }
            }

            if deep and hasattr(fixture.plugin, 'info'):
                plugin_info = fixture.plugin.info()
                if isinstance(plugin_info, dict):
                    info.update(plugin_info)

            list.append(info)

        return json.dumps(list, indent=2)
