"""

Mirantis MSR API Client

"""

import logging
import json
from typing import List, Dict
import requests
from enum import Enum

from mirantis.testing.metta.plugin import Type
from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.client import ClientBase
from mirantis.testing.metta.cli import CliBase

logger = logging.getLogger('metta.contrib.metta_mirantis.client.msrapi')


METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID = 'metta_mirantis_client_msr'
""" Mirantis MSR APIP Client plugin id """


class MSRAPICliPlugin(CliBase):

    def fire(self):
        """ return a dict of commands for aucnhpad provisioenrs if one hase been registered."""
        if self.environment.fixtures.get_fixture(
                type=Type.CLIENT, plugin_id=METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID, exception_if_missing=False) is not None:
            return {
                'contrib': {
                    'msr': MSRAPICliGroup(self.environment)
                }
            }
        else:
            return {}


class MSRAPICliGroup():

    def __init__(self, environment: Environment):
        self.environment = environment

    def _select_fixture(self, instance_id: str = ''):
        """ Pick a matching fixture in case there are more than one """
        if instance_id:
            return self.environment.fixtures.get_fixture(
                type=Type.CLIENT, plugin_id=METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID, instance_id=instance_id)
        else:
            # Get the highest priority fixture
            return self.environment.fixtures.get_fixture(
                type=Type.CLIENT, plugin_id=METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID)

    def info(self, instance_id: str = '', deep: bool = False):
        """ get info about a plugin """
        fixture = self._select_fixture(instance_id=instance_id)

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
                info.update(fixture.plugin.info(deep))

        return json.dumps(info, indent=2)

    def version(self, instance_id: str = ''):
        """ get MSR cluster version """
        fixture = self._select_fixture(instance_id=instance_id)
        plugin = fixture.plugin
        return json.dumps(plugin.api_version(), indent=2)

    def status(self, instance_id: str = ''):
        """ get clsuter status """
        fixture = self._select_fixture(instance_id=instance_id)
        plugin = fixture.plugin
        return json.dumps(plugin.api_status(), indent=2)

    def features(self, instance_id: str = ''):
        """ get features list """
        fixture = self._select_fixture(instance_id=instance_id)
        plugin = fixture.plugin
        return json.dumps(plugin.api_features(), indent=2)

    def alerts(self, instance_id: str = ''):
        """ get alerts list """
        fixture = self._select_fixture(instance_id=instance_id)
        plugin = fixture.plugin
        return json.dumps(plugin.api_alerts(), indent=2)


class MSRReplicaHealth(Enum):
    """ MSR replica health in the cluster status API response """
    OK = 'OK'

    def match(self, compare: str) -> bool:
        """ allow for string comparisons """
        return self.value == compare


class MSRAPIClientPlugin(ClientBase):
    """ Client for API Connections to MSR """

    def __init__(self, environment: Environment, instance_id: str, accesspoint: str,
                 username: str, password: str, hosts: List[Dict], api_version: str = 'v0'):
        """

        Parameters:
        -----------


        """
        self.accesspoint = accesspoint
        self.username = username
        self.password = password

        self.hosts = hosts
        """ List of hosts """

        if not self.accesspoint:
            # use the first host as an accesspoint if none was delivered
            self.accesspoint = self._node_address(0)

        self.version = api_version
        """ used to build the api url """

        self.verify = False
        """ should we verify ssl certs """
        if not self.verify:
            requests.packages.urllib3.disable_warnings(
                requests.packages.urllib3.exceptions.InsecureRequestWarning)

        self.auth_token = None
        """ hold the bearer auth token if created by ._auth_headers() """

    def info(self, deep: bool = False):
        """ return information about the plugin """
        info = {
            'api': {
                'accesspoint': self.accesspoint,
                'username': self.username,
            },
            'hosts': self.hosts
        }

        if deep:
            info['version'] = self.api_version()
            info['features'] = self.api_features()
            info['status'] = self.api_status()

        return info

    def api_version(self) -> Dict:
        """ retrieve version """
        with requests.get(self._accesspoint_url('admin/version'), auth=self._api_auth(), verify=self.verify) as response:
            response.raise_for_status()
            return json.loads(response.content)

    def api_status(self) -> Dict:
        """ retrieve status from the api """
        with requests.get(self._accesspoint_url('meta/cluster_status'), auth=self._api_auth(), verify=self.verify) as response:
            response.raise_for_status()
            return json.loads(response.content)

    def api_features(self) -> Dict:
        """ retrieve features list from the api """
        with requests.get(self._accesspoint_url('meta/features'), auth=self._api_auth(), verify=self.verify) as response:
            response.raise_for_status()
            return json.loads(response.content)

    def api_alerts(self) -> Dict:
        """ retrieve alerts list from the api """
        with requests.get(self._accesspoint_url('meta/alerts'), auth=self._api_auth(), verify=self.verify) as response:
            response.raise_for_status()
            return json.loads(response.content)

    def _api_auth(self):
        """ get the requests auth handler """
        return requests.auth.HTTPBasicAuth(self.username, self.password)

    def _accesspoint_url(self, endpoint: str = ''):
        """ convert an endpoint into a full URL for the LB/AccessPoint """
        return "https://{accesspoint}/api/{version}/{endpoint}".format(
            accesspoint=self.accesspoint, version=self.version, endpoint=endpoint)

    def _node_url(self, node: int, endpoint: str = ''):
        """ convert an endpoint into a full URL for a specific node """
        return "https://{accesspoint}/api/{version}/{endpoint}".format(
            accesspoint=self._node_address(node), version=self.version, endpoint=endpoint)

    def _node_address(self, node: int = 0):
        """ get the ip address from the node for the node index """
        node = self.hosts[node]
        if 'address' in node:
            return node['address']
        elif 'ssh' in node:
            return node['ssh']['address']
        elif 'winrm' in node:
            return node['winrm']['address']
