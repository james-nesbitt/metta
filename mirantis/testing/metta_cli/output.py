import logging
from typing import Dict, Any, List

import json

from mirantis.testing.metta.plugin import Type
from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.cli import CliBase

logger = logging.getLogger('metta.cli.output')


class OutputCliPlugin(CliBase):

    def fire(self):
        """ return a dict of commands """
        return {
            'output': OutputGroup(self.environment)
        }


class OutputGroup():

    def __init__(self, environment: Environment):
        self.environment = environment

    def list(self):
        """ List all outputs """
        list = [
            plugin.instance_id for plugin in self.environment.fixtures.fixtures(
                type=Type.OUTPUT)]

        json.dumps(list)

    def info(self, plugin_id: str = '',
             instance_id: str = '', deep: bool = False):
        """ List all outputs """
        details = []
        for plugin in self.environment.fixtures.get_plugins(type=Type.OUTPUT):
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

        json.dumps(list)
