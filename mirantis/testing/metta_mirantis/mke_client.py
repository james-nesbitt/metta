"""

Mirantis MKE API Client

"""

import logging
import requests
import json
import toml
from typing import Dict, List
from enum import Enum

from mirantis.testing.metta.plugin import Type
from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.client import ClientBase
from mirantis.testing.metta.cli import CliBase


logger = logging.getLogger('metta.contrib.metta_mirantis.client.mkeapi')


METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID = 'metta_mirantis_client_mke'
""" Mirantis MKE API Client plugin id """


class MKEAPICliPlugin(CliBase):
    """ Metta CLI plugin which injects the MKE API Client CLI commands into the CLI handler """

    def fire(self):
        """ return a dict of commands for aucnhpad provisioenrs if one hase been registered."""
        if self.environment.fixtures.get_fixture(
                type=Type.CLIENT, plugin_id=METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID, exception_if_missing=False) is not None:
            return {
                'contrib': {
                    'mke': MKEAPICliGroup(self.environment)
                }
            }
        else:
            return {}


class MKEAPICliGroup():
    """ Metta CLI plugin which actually provides the MKE API Client CLI commands """

    def __init__(self, environment: Environment):
        self.environment = environment

    def _select_fixture(self, instance_id: str = ''):
        """ Pick a matching fixture in case there are more than one """
        if instance_id:
            return self.environment.fixtures.get_fixture(
                type=Type.CLIENT, plugin_id=METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID, instance_id=instance_id)
        else:
            # Get the highest priority fixture
            return self.environment.fixtures.get_fixture(
                type=Type.CLIENT, plugin_id=METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID)

    def info(self, instance_id: str = '', deep: bool = False):
        """ get info about a plugin """
        fixture = self._select_fixture(instance_id=instance_id)
        plugin = fixture.plugin

        info = {
            'fixture': {
                'type': fixture.type.value,
                'plugin_id': fixture.plugin_id,
                'instance_id': fixture.instance_id,
                'priority': fixture.priority,
            }
        }

        info.update(plugin.info(deep))

        return json.dumps(info, indent=2)

    def version(self, instance_id: str = ''):
        """ get info about a plugin """
        fixture = self._select_fixture(instance_id=instance_id)
        plugin = fixture.plugin
        return json.dumps(plugin.api_version(), indent=2)

    def ping(self, instance_id: str = '', node: int = None):
        """ check if we can ping """
        fixture = self._select_fixture(instance_id=instance_id)
        plugin = fixture.plugin
        return "OK" if plugin.api_ping(node) else "FAIL"

    def pingall(self, instance_id: str = ''):
        """ check if we can ping all of the nodes directly """
        fixture = self._select_fixture(instance_id=instance_id)
        plugin = fixture.plugin
        ping = {}
        for index in range(0, plugin.host_count()):
            try:
                plugin.api_ping(index)
                ping[plugin._node_address(index)] = True
            except BaseException:
                ping[plugin._node_address(index)] = False

        return json.dumps(ping, indent=2)

    def id(self, instance_id: str = ''):
        """ get auth id """
        fixture = self._select_fixture(instance_id=instance_id)
        plugin = fixture.plugin
        return json.dumps(plugin.api_id(), indent=2)

    def nodes(self, instance_id: str = '', node_id: str = ''):
        """ list swarm nodes """
        fixture = self._select_fixture(instance_id=instance_id)
        plugin = fixture.plugin
        return json.dumps(plugin.api_nodes(node_id), indent=2)

    def services(self, instance_id: str = '', service_id: str = ''):
        """ list swarm services """
        fixture = self._select_fixture(instance_id=instance_id)
        plugin = fixture.plugin
        return json.dumps(plugin.api_services(service_id), indent=2)

    def tasks(self, instance_id: str = '', task_id: str = ''):
        """ list swarm tasks """
        fixture = self._select_fixture(instance_id=instance_id)
        plugin = fixture.plugin
        if task_id:
            return json.dumps(plugin.api_task(task_id), indent=2)
        else:
            return json.dumps(plugin.api_tasks(), indent=2)

    def tomlconfig(self, instance_id: str = ''):
        """ get the toml config """
        fixture = self._select_fixture(instance_id=instance_id)
        plugin = fixture.plugin
        return json.dumps(plugin.api_ucp_configtoml_get(), indent=2)

    def tomlconfig_set(self, table: str, key: str,
                       value: str, instance_id: str = ''):
        """ set a single toml config value """
        fixture = self._select_fixture(instance_id=instance_id)
        plugin = fixture.plugin

        data = plugin.api_ucp_configtoml_get()
        data[table][key] = value
        return json.dumps(plugin.api_ucp_configtoml_put(data), indent=2)

    def metricsdiscovery(self, instance_id: str = ''):
        """ get the api metrics-discover """
        fixture = self._select_fixture(instance_id=instance_id)
        plugin = fixture.plugin
        return json.dumps(plugin.api_metrics_discovery(), indent=2)

    def metrics(self, instance_id: str = ''):
        """ get the toml config """
        fixture = self._select_fixture(instance_id=instance_id)
        plugin = fixture.plugin
        return json.dumps(plugin.api_metrics_discovery(), indent=2)

    def auth(self, instance_id: str = ''):
        """ retrieve auth headersg """
        fixture = self._select_fixture(instance_id=instance_id)
        plugin = fixture.plugin
        return json.dumps(plugin._auth_headers(), indent=2)


class MKENodeState(Enum):
    """ MKE Node state in the node status API response """
    UNKNOWN = 'unknown'
    DOWN = 'down'
    READY = 'ready'
    DISCONNECTED = 'disconnected'

    def match(self, compare: str) -> bool:
        """ allow for string comparisons """
        return self.value == compare


class MKEAPIClientPlugin(ClientBase):
    """ Metta Client plugin for API Connections to MKE """

    def __init__(self, environment: Environment, instance_id: str,
                 accesspoint: str, username: str, password: str, hosts: List[Dict]):
        """

        Parameters:
        -----------

        Standard Metta plugin parameters:

        environment (Environment) : env in which this plugin exists
            can be used to get access to config, other fixtures etc.
        instance_id (str) : string ID for this plugin to self-identify

        Plugin specific parameters:

        accesspoint (str) : API URL endpoint

        username / password (str/str) : API authentication credentials

        hosts (List[Dict]) : List of host definition dicts used to define hosts
            that can respond to API requests in the cluster.  This can be used
            to allow directly accessing the API through a specific host.
            The first node in the list is used as an API endpoint if no endpoint
            is specified.

        """
        ClientBase.__init__(self, environment, instance_id)

        self.accesspoint = accesspoint
        self.username = username
        self.password = password

        self.hosts = hosts
        """ List of hosts """

        if self.accesspoint is None:
            # use the first host as an accesspoint if none was delivered
            self.accesspoint = self._node_address(0)

        self.verify = False
        """ should we verify ssl certs """
        if not self.verify:
            requests.packages.urllib3.disable_warnings(
                requests.packages.urllib3.exceptions.InsecureRequestWarning)

        self.auth_token = None
        """ hold the bearer auth token if created by ._auth_headers() (cache) """

    def host_count(self):
        """ Return integer host count for MKE cluster """
        return len(self.hosts)

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
            info['id'] = self.api_id()
            info['version'] = self.api_version()
            info['api_info'] = self.api_info()

        return info

    def auth_header(self) -> Dict:
        """ retrieve the auth headers so you can do your own thing. """
        return json.loads(self._auth_headers())

    def api_ping(self, node: int = None) -> bool:
        """ Check the API ping response """
        if node is not None:
            endpoint = self._accesspoint_url('_ping', node=node)
        else:
            endpoint = self._accesspoint_url('_ping')

        with requests.get(endpoint, verify=self.verify) as response:
            response.raise_for_status()
            return response.ok

    def api_id(self) -> Dict:
        """ retrieve the API id """
        with requests.get(self._accesspoint_url('id'), headers=self._auth_headers(), verify=self.verify) as response:
            response.raise_for_status()
            return json.loads(response.content)

    def api_version(self) -> Dict:
        """ retrieve version """
        with requests.get(self._accesspoint_url('version'), headers=self._auth_headers(), verify=self.verify) as response:
            response.raise_for_status()
            return json.loads(response.content)

    def api_info(self) -> Dict:
        """ retrieve the API info """
        with requests.get(self._accesspoint_url('info'), headers=self._auth_headers(), verify=self.verify) as response:
            response.raise_for_status()
            return json.loads(response.content)

    def api_nodes(self, node_id: str = '') -> Dict:
        """ retrieve the API nodes """
        endpoint = 'nodes/{id}'.format(id=node_id) if node_id else 'nodes'
        with requests.get(self._accesspoint_url(endpoint), headers=self._auth_headers(), verify=self.verify) as response:
            response.raise_for_status()
            return json.loads(response.content)

    def api_services(self, service_id: str = '') -> Dict:
        """ retrieve the API services """
        endpoint = 'services/{id}'.format(
            id=service_id) if service_id else 'services'
        with requests.get(self._accesspoint_url(endpoint), headers=self._auth_headers(), verify=self.verify) as response:
            response.raise_for_status()
            return json.loads(response.content)

    def api_metrics_discovery(self):
        """ retrieve the API metrics """
        endpoint = 'metricsdiscovery'
        with requests.get(self._accesspoint_url(endpoint), headers=self._auth_headers(), verify=self.verify) as response:
            response.raise_for_status()
            return json.loads(response.content)

    def api_tasks(self):
        """ retrieve the API tasks """
        endpoint = 'tasks'
        with requests.get(self._accesspoint_url(endpoint), headers=self._auth_headers(), verify=self.verify) as response:
            response.raise_for_status()
            return json.loads(response.content)

    def api_task(self, task_id: str):
        """ retrieve the API tasks """
        endpoint = 'tasks/{id}'.format(id=task_id)
        with requests.get(self._accesspoint_url(endpoint), headers=self._auth_headers(), verify=self.verify) as response:
            response.raise_for_status()
            return json.loads(response.content)

    def api_ucp_configtoml_get(self):
        """ retrieve config toml as a struct """
        endpoint = 'api/ucp/config-toml'
        with requests.get(self._accesspoint_url(endpoint), headers=self._auth_headers(), verify=self.verify) as response:
            response.raise_for_status()
            return toml.loads(response.text)

    def api_ucp_configtoml_put(self, data):
        """ send struct config as a toml string """
        endpoint = 'api/ucp/config-toml'
        data_toml = toml.dumps(data)
        with requests.put(self._accesspoint_url(endpoint), headers=self._auth_headers(), verify=self.verify, data=data_toml) as response:
            response.raise_for_status()
            return {'response': json.loads(response.content), 'data': data}

    def _auth_headers(self):
        """ get an auth token """
        if self.auth_token is None:
            data = {
                "password": self.password,
                "username": self.username
            }
            with requests.post(self._accesspoint_url('auth/login'), data=json.dumps(data), verify=self.verify) as response:
                response.raise_for_status()
                content = json.loads(response.content)
                self.auth_token = content['auth_token']

        return {'Authorization': 'Bearer {auth_token}'.format(
            auth_token=self.auth_token)}

    def _accesspoint_url(self, endpoint: str = '', node: int = None):
        """ convert an endpoint into a full URL for an API Call

        Pass in a sub-url endpoint and this will convert it into a full URL.
        You can request a specific host index if desired.

        Parameters:
        -----------

        endpoint (str) : API endpoint you are trying to access

        node (int) : If not None, then the API call should be directed to a specific
            node index from the list of hosts, as opposed to the generic accesspoint.
            This allows things like ping confirmation on specific host.

        """
        if node is None:
            target = self.accesspoint
        else:
            target = self._node_address(node)

        return "https://{accesspoint}/{endpoint}".format(
            accesspoint=target.rstrip('/'), endpoint=endpoint.lstrip('/'))

    def _node_address(self, node: int = 0):
        """ get the ip address from the node for the node index """
        node = self.hosts[node]
        if 'address' in node:
            return node['address']
        elif 'ssh' in node:
            return node['ssh']['address']
        elif 'winrm' in node:
            return node['winrm']['address']
