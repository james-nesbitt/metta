import logging
from typing import Dict, Any

import json
import yaml

from uctt.plugin import Type
from uctt.environment import Environment
from uctt.cli import CliBase
from uctt_cli.provisioner import ProvisionerGroup

logger = logging.getLogger('uctt.cli.launchpad')


class LaunchpadCliPlugin(CliBase):

    def fire(self):
        """ return a dict of commands """
        if self.environment.fixtures.get_fixture(type=Type.PROVISIONER, plugin_id='mtt_launchpad') is not None:
            return {
                'launchpad': LaunchpadGroup(self.environment)
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
                type=Type.PROVISIONER, plugin_id='mtt_launchpad', instance_id=instance_id)
        else:
            # Get the highest priority provisioner
            return self.environment.fixtures.get_fixture(type=Type.PROVISIONER, plugin_id='mtt_launchpad')

    def info(self, provisioner: str = ''):
        """ get info about a provisioner plugin """
        fixture = self._select_provisioner(instance_id=provisioner)
        plugin = fixture.plugin
        backend_fixture = plugin.backend_fixture
        client = plugin.client
        info = {
            'fixture': {
                'type': fixture.type.value,
                'plugin_id': fixture.plugin_id,
                'instance_id': fixture.instance_id,
                'priority': fixture.priority
            },
            'plugin': {
                'config_label': plugin.config_label,
                'config_base': plugin.config_base,
                'downloaded_bundle_users': plugin.downloaded_bundle_users,
                'working_dir': plugin.working_dir,
                'backend_output_name': plugin.backend_output_name,
                'is_provisioned': plugin.is_provisioned,
                'is_installed': plugin.is_installed
            },
            'backend': {
                'type': backend_fixture.type.value,
                'plugin_id': backend_fixture.plugin_id,
                'instance_id': backend_fixture.instance_id,
                'priority': backend_fixture.priority
            },
            'client': {
                'cluster_name_override': client.cluster_name_override,
                'config_file': client.config_file,
                'working_dir': client.working_dir,
                'bin': client.bin
            },
            'helper': {
                'commands': {
                    'apply': "{workingpathcd}{bin} apply -c {config_file}".format(workingpathcd=("cd {} &&".format(client.working_dir) if not client.working_dir=='.' else '') , bin=client.bin, config_file=client.config_file),
                    'client-config': "{workingpathcd}{bin} client-config -c {config_file} {user}".format(workingpathcd=("cd {} &&".format(client.working_dir) if not client.working_dir=='.' else '') , bin=client.bin, config_file=client.config_file, user='admin')
                }
            }
        }

        return json.dumps(info, indent=2)

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
            raise ValueError("Launchpad yaml file had unexpected contents: {}".format(e)) from e

        return json.dumps(config_data, indent=2)

    def output(self, output: str, provisioner: str = ''):
        """ Interact with provisioner outputs """
        provisioner = self._select_provisioner(instance_id=provisioner).plugin
        if not hasattr(provisioner, 'get_output'):
            raise ValueError('This provisioner does not keep outputs.')

        plugin = provisioner.get_output(instance_id=output)

        if not hasattr(plugin, 'get_output'):
            raise ValueError(
                "Found output '{}' but is cannot be exported in the cli.".format(
                    plugin.instance_id))

        return json.dumps(plugin.get_output(), indent=2)

    def fixtures(self, provisioner: str = '', type: Type = None, plugin_id: str = '',
                   instance_id: str = ''):
        """ List all outputs """
        provisioner = self._select_provisioner(instance_id=provisioner).plugin
        if not hasattr(provisioner, 'get_fixtures'):
            raise ValueError('This provisioner does not keep fixtures.')
        list = [{
            'type': fixture.type.value,
            'plugin_id': fixture.plugin_id,
            'instance_id': fixture.instance_id,
            'priority': fixture.priority,
        } for fixture in provisioner.get_fixtures(type=Type.from_string(type), plugin_id=plugin_id, instance_id=instance_id)]

        return json.dumps(list, indent=2)

    def client_bundle(self, provisioner: str = '',user: str = 'admin'):
        """ Tell Launchpad to download the client bundle """
        fixture = self._select_provisioner(instance_id=provisioner)
        plugin = fixture.plugin

        logger.info("Downloading client bungle for user: {}".format(user))
        try:
            bundle = plugin._mke_client_bundle(user=user)
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
        provisioner.prepare()
        provisioner.apply()

    def destroy(self, provisioner: str = ''):
        """ Run provisioner destroy """
        provisioner = self._select_provisioner(instance_id=provisioner).plugin
        provisioner.prepare()
        provisioner.destroy()
