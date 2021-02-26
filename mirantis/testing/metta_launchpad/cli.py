import logging
from typing import Dict, Any

import json
import yaml

from mirantis.testing.metta.plugin import Type
from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.cli import CliBase
from mirantis.testing.metta_cli.provisioner import ProvisionerGroup

logger = logging.getLogger('metta.cli.launchpad')


class LaunchpadCliPlugin(CliBase):

    def fire(self):
        """ return a dict of commands for aucnhpad provisioenrs if one hase been registered."""
        if self.environment.fixtures.get_fixture(
                type=Type.PROVISIONER, plugin_id='metta_launchpad', exception_if_missing=False) is not None:
            return {
                'contrib': {
                    'launchpad': LaunchpadGroup(self.environment)
                }
            }
        else:
            return {}


class LaunchpadGroup():

    def __init__(self, environment: Environment):
        self.environment = environment

    def _select_provisioner(self, instance_id: str = ''):
        """ Pick a matching provisioner """
        if instance_id:
            return self.environment.fixtures.get_fixture(
                type=Type.PROVISIONER, plugin_id='metta_launchpad', instance_id=instance_id)
        else:
            # Get the highest priority provisioner
            return self.environment.fixtures.get_fixture(
                type=Type.PROVISIONER, plugin_id='metta_launchpad')

    def info(self, provisioner: str = '', deep: bool = False):
        """ get info about a provisioner plugin """
        fixture = self._select_provisioner(instance_id=provisioner)

        provisioner_info = {
            'fixture': {
                'type': fixture.type.value,
                'plugin_id': fixture.plugin_id,
                'instance_id': fixture.instance_id,
                'priority': fixture.priority,
            }
        }

        if deep:
            if hasattr(fixture.plugin, 'info'):
                provisioner_info.update(fixture.plugin.info(True))

        return json.dumps(provisioner_info, indent=2)

    def hosts(self, provisioner: str = '', deep: bool = False):
        """ list the hosts in the cluster """
        fixture = self._select_provisioner(instance_id=provisioner)
        plugin = fixture.plugin
        client = plugin.client

        config = client.describe_config()

        if deep:
            list = [host for host in config['spec']['hosts']]
        else:
            list = []
            for host in config['spec']['hosts']:
                list_host = {
                    'role': host['role']
                }
                if 'ssh' in host:
                    list_host.update({
                        'is_windows': False,
                        'address': host['ssh']['address']
                    })
                if 'winrm' in host:
                    list_host.update({
                        'is_windows': True,
                        'address': host['winrm']['address']
                    })

                list.append(list_host)

        return json.dumps(list, indent=2)

    def exec(self, cmd: str, provisioner: str = '',
             host: int = 0, interactive: bool = False):
        """ Exec a command """
        fixture = self._select_provisioner(instance_id=provisioner)
        plugin = fixture.plugin
        client = plugin.client

        cmds = cmd.split(' ')

        client.exec(host_index=host, cmds=cmds)

    def exec_interactive(self, cmd: str, provisioner: str = '',
                         host: int = 0, interactive: bool = False):
        """ Exec a command """
        fixture = self._select_provisioner(instance_id=provisioner)
        plugin = fixture.plugin
        client = plugin.client

        cmds = cmd.split(' ')

        client.exec_interactive(host_index=host, cmds=cmds)

    def fixtures(self, provisioner: str = ''):
        """ List all fixtures for this provisioner """
        provisioner = self._select_provisioner(instance_id=provisioner).plugin
        if not hasattr(provisioner, 'get_fixtures'):
            raise ValueError('This provisioner does not keep fixtures.')
        list = [{
            'type': fixture.type.value,
            'plugin_id': fixture.plugin_id,
            'instance_id': fixture.instance_id,
            'priority': fixture.priority,
        } for fixture in provisioner.get_fixtures().to_list()]

        json.dumps(list, indent=2)

    def config_file(self, provisioner: str = ''):
        """ get info about a provisioner plugin """
        fixture = self._select_provisioner(instance_id=provisioner)
        plugin = fixture.plugin
        backend_fixture = plugin.backend_fixture
        client = plugin.client

        try:
            with open(client.config_file) as f:
                config_data = yaml.load(f, Loader=yaml.FullLoader)
                """ parsed the launchpad file """
        except Exception as e:
            raise ValueError(
                "Launchpad yaml file had unexpected contents: {}".format(e)) from e

        return json.dumps(config_data, indent=2)

    def version(self, provisioner: str = ''):
        """ Output a launchpad cli report """
        provisioner = self._select_provisioner(instance_id=provisioner).plugin
        provisioner.client.version()

    def describe(self, report: str, provisioner: str = ''):
        """ Output a launchpad cli report """
        provisioner = self._select_provisioner(instance_id=provisioner).plugin
        provisioner.client.describe(report)

    def fixtures(self, provisioner: str = '', type: Type = None, plugin_id: str = '',
                 instance_id: str = ''):
        """ List all outputs """
        provisioner = self._select_provisioner(instance_id=provisioner).plugin
        if not hasattr(provisioner, 'get_fixtures'):
            raise ValueError('This provisioner does not keep fixtures.')

        type = Type.from_string(type) if type else None

        list = [{
            'type': fixture.type.value,
            'plugin_id': fixture.plugin_id,
            'instance_id': fixture.instance_id,
            'priority': fixture.priority,
        } for fixture in provisioner.get_fixtures(type=type, plugin_id=plugin_id, instance_id=instance_id).to_list()]

        return json.dumps(list, indent=2)

    def config_file(self, provisioner: str = ''):
        """ Dump the config file """
        provisioner = self._select_provisioner(instance_id=provisioner).plugin

        try:
            with open(provisioner.config_file) as f:
                config_contents = yaml.load(f)
        except FileNotFoundError as e:
            raise ValueError("No config file was found: {}".format(e)) from e

        return json.dumps(config_contents, indent=2)

    def client_bundle(self, provisioner: str = '',
                      user: str = 'admin', reload: bool = False):
        """ Tell Launchpad to download the client bundle """
        fixture = self._select_provisioner(instance_id=provisioner)
        plugin = fixture.plugin

        logger.info("Downloading client bungle for user: {}".format(user))
        try:
            bundle = plugin._mke_client_bundle(user=user, reload=reload)
        except Exception as e:
            raise Exception("Launchpad command failed : {}".format(e)) from e

        return json.dumps(bundle, indent=2)

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
