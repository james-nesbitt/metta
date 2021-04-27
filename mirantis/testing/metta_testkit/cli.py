import logging
from typing import Dict, Any

import json

from mirantis.testing.metta.plugin import Type
from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.cli import CliBase

logger = logging.getLogger('metta.cli.testkit')

METTA_PLUGIN_ID_TESTKIT_CLI = 'testkit'

class TestkitCliPlugin(CliBase):

    def fire(self):
        """ return a dict of commands """
        if self.environment.fixtures.get_fixture(
                type=Type.PROVISIONER, plugin_id='metta_testkit', exception_if_missing=False) is not None:
            return {
                'contrib': {
                    'testkit': TestkitGroup(self.environment)
                }
            }
        else:
            return {}


class TestkitGroup():

    def __init__(self, environment: Environment):
        self.environment = environment


    def _select_provisioner(self, instance_id: str = ''):
        """ Pick a matching provisioner (in case you have more than one testkit provisioner configured) """
        if instance_id:
            return self.environment.fixtures.get_fixture(
                type=Type.PROVISIONER, plugin_id='metta_testkit', instance_id=instance_id)
        else:
            # Get the highest priority provisioner
            return self.environment.fixtures.get_fixture(
                type=Type.PROVISIONER, plugin_id='metta_testkit')


    def info(self, provisioner: str = '', deep: bool = False):
        """ get info about a provisioner plugin """
        fixture = self._select_provisioner(instance_id=provisioner)

        info = {
            'fixture': {
                'type': fixture.type.value,
                'plugin_id': fixture.plugin_id,
                'instance_id': fixture.instance_id,
                'priority': fixture.priority,
            }
        }

        if deep:
            if hasattr(fixture.plugin, 'info'):
                info.update(fixture.plugin.info(True))

        return json.dumps(info, indent=2)

    def prepare(self, provisioner: str = ''):
        """ Run the provisioner prepare : which for testkit currently does nothing """
        pass

    def apply(self, provisioner: str = ''):
        """ Run the provisioner apply, which runs testkit create """
        plugin = self._select_provisioner(instance_id=provisioner).plugin
        return json.dumps(plugin.apply())

    def destroy(self, provisioner: str = ''):
        """ Run the provisioner destroy, which runs testkit system rm """
        plugin = self._select_provisioner(instance_id=provisioner).plugin
        return json.dumps(plugin.destroy())
