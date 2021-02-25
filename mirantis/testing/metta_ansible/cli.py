import logging
from typing import Dict, Any

import json

from mirantis.testing.metta.plugin import Type
from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.cli import CliBase
from mirantis.testing.metta_cli.provisioner import ProvisionerGroup

logger = logging.getLogger('metta.cli.ansible')


class AnsibleCliPlugin(CliBase):

    def fire(self):
        """ return a dict of commands """
        if self.environment.fixtures.get_fixture(
                type=Type.PROVISIONER, plugin_id='metta_ansible', exception_if_missing=False) is not None:
            return {
                'contrib': {
                    'ansible': AnsibleGroup(self.environment)
                }
            }
        else:
            return {}


class AnsibleGroup():

    def __init__(self, environment: Environment):
        self.environment = environment

    def _select_provisioner(self, instance_id: str = ''):
        """ Pick a matching provisioner """
        if instance_id:
            return self.environment.fixtures.get_fixture(
                type=Type.PROVISIONER, plugin_id='metta_ansible', instance_id=instance_id)
        else:
            # Get the highest priority provisioner
            return self.environment.fixtures.get_fixture(
                type=Type.PROVISIONER, plugin_id='metta_ansible')

    def info(self, provisioner: str = ''):
        """ get info about a provisioner plugin """
        fixture = self._select_provisioner(instance_id=provisioner)
        plugin = fixture.plugin

        info = {
            'fixture': {
                'type': fixture.type.value,
                'plugin_id': fixture.plugin_id,
                'instance_id': fixture.instance_id,
                'priority': fixture.priority
            }
        }
        info.update(plugin.info())

        return json.dumps(info, indent=2)

    def prepare(self, provisioner: str = ''):
        """ Run provisioner prepare """
        provisioner = self._select_provisioner(instance_id=provisioner).plugin
        provisioner.prepare()

    def apply(self, provisioner: str = ''):
        """ Run provisioner apply """
        provisioner = self._select_provisioner(instance_id=provisioner).plugin
        provisioner.apply()

    def destroy(self, provisioner: str = ''):
        """ Run provisioner destroy """
        provisioner = self._select_provisioner(instance_id=provisioner).plugin
        provisioner.destroy()
