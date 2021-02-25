import logging
from typing import Dict, Any

import json

from mirantis.testing.metta.plugin import Type
from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.cli import CliBase

from .output import OutputGroup

logger = logging.getLogger('metta.cli.provisioner')


class ProvisionerCliPlugin(CliBase):

    def fire(self):
        """ return a dict of commands """
        return {
            'provisioner': ProvisionerGroup(self.environment)
        }


class ProvisionerGroup():

    def __init__(self, environment: Environment):
        self.environment = environment

    def list(self, raw: bool = False):
        """ List all provisioners """
        list = [
            plugin.instance_id for plugin in self.environment.fixtures.get_plugins(
                type=Type.PROVISIONER)]

        if raw:
            return list
        else:
            return json.dumps(list)

    def _select_provisioner(self, instance_id: str = ''):
        """ Pick a matching provisioner """
        if instance_id:
            return self.environment.fixtures.get_fixture(
                type=Type.PROVISIONER, instance_id=instance_id)
        else:
            # Get the highest priority provisioner
            return self.environment.fixtures.get_fixture(type=Type.PROVISIONER)

    def info(self, provisioner: str = '', deep: bool = True):
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
                plugin_info = fixture.plugin.info()
                if isinstance(plugin_info, dict):
                    info.update(plugin_info)

            if hasattr(fixture.plugin, 'get_fixtures'):
                fixtures = {}
                for sub_fixture in fixture.plugin.get_fixtures().to_list():
                    fixture_info = {
                        'fixture': {
                            'type': sub_fixture.type.value,
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

        return json.dumps(info, indent=2, default=lambda X: "{}".format(X))

    def fixtures(self, provisioner: str = '', deep: bool = False):
        """ List all fixtures for this provisioner """
        provisioner = self._select_provisioner(instance_id=provisioner).plugin
        if not hasattr(provisioner, 'get_fixtures'):
            raise ValueError('This provisioner does not keep fixtures.')

        list = {}
        for fixture in provisioner.get_fixtures().to_list():

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
                    plugin_info = fixture.plugin.info()
                    if isinstance(plugin_info, dict):
                        info.update(plugin_info)

                if hasattr(fixture.plugin, 'get_fixtures'):
                    fixtures = {}
                    for sub_fixture in fixture.plugin.get_fixtures().to_list():
                        fixture_info = {
                            'fixture': {
                                'type': sub_fixture.type.value,
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

            list[fixture.instance_id] = info

        return json.dumps(list, indent=2)

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
