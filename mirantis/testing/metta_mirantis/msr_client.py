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
    """ MEtta CLI plugin for injecting MSR API Client commands into the cli """

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
    """ MSR API Client CLI commands """

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

    def ping(self, instance_id: str = '', node: int = None):
        """ ping an MSR replica """
        fixture = self._select_fixture(instance_id=instance_id)
        plugin = fixture.plugin
        return json.dumps(plugin.api_ping(node=node), indent=2)

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

    def health(self, instance_id: str = '', node: int = None):
        """ Get the MSR health api response """
        fixture = self._select_fixture(instance_id=instance_id)
        plugin = fixture.plugin
        return json.dumps(plugin.api_health(node=node), indent=2)

    def nginx_status(self, instance_id: str = '', node: int = None):
        """ Get the MSR nginsx status api response """
        fixture = self._select_fixture(instance_id=instance_id)
        plugin = fixture.plugin
        return json.dumps(plugin.api_nginx_status(node=node), indent=2)

    def version(self, instance_id: str = ''):
        """ get MSR cluster version """
        fixture = self._select_fixture(instance_id=instance_id)
        plugin = fixture.plugin
        return json.dumps(plugin.api_version(), indent=2)

    def status(self, instance_id: str = ''):
        """ get cluster status """
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
    """ MSR replica health values (in the cluster status API response) """
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
        """ should we verify ssl certs : default to NO """
        if not self.verify:
            requests.packages.urllib3.disable_warnings(
                requests.packages.urllib3.exceptions.InsecureRequestWarning)

        self.auth_token = None
        """ hold the bearer auth token if created by ._auth_headers() """

    def host_count(self):
        """ Return integer host count for MSR cluster """
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
            info['version'] = self.api_version()
            info['features'] = self.api_features()
            info['status'] = self.api_status()

        return info

    def api_ping(self, node: int = None) -> bool:
        """ Check the API ping response """
        endpoint = self._accesspoint_url('_ping', root_api=True, node=node)

        with requests.get(endpoint, verify=self.verify) as response:
            response.raise_for_status()
            return response.ok

    def api_health(self, node: int = None):
        """ Check the API ping response """
        endpoint = self._accesspoint_url('health', root_api=True, node=node)

        with requests.get(endpoint, auth=self._api_auth(), verify=self.verify) as response:
            response.raise_for_status()
            return json.loads(response.content)

    def api_nginx_status(self, node: int = None):
        """ Check the API ping response

        returns:

        parsed string contents of the response

        """
        endpoint = self._accesspoint_url(
            'nginx_status', root_api=True, node=node)

        with requests.get(endpoint, auth=self._api_auth(), headers={'content-type': 'application/json'}, verify=self.verify) as response:
            response.raise_for_status()
            # @TODO should we parse this?
            return response.content.decode("utf-8")

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

    def _accesspoint_url(self, endpoint: str = '',
                         root_api: bool = False, node: int = None):
        """ convert an endpoint into a full URL for an API Call

        Pass in a sub-url endpoint and this will convert it into a full URL.
        Most endpoints will have the api/v0/ prefix added (unless it is a root
        API call) and will get passed on to the configured accesspoint.

        You can request a specific host index if desired.

        Parameters:
        -----------

        endpoint (str) : API endpoint you are trying to access

        root_api (bool) : If True, then the URL should be for a root API call
            which doesn't have any version info

        node (int) : If not None, then the API call should be directed to a specific
            node index from the list of hosts, as opposed to the generic accesspoint.
            This allows things like ping confirmation on specific host.

        """
        if node is None:
            target = self.accesspoint
        else:
            target = self._node_address(node)

        if root_api:
            return "https://{accesspoint}/{endpoint}".format(
                accesspoint=target, endpoint=endpoint)
        else:
            return "https://{accesspoint}/api/{version}/{endpoint}".format(
                accesspoint=target, version=self.version, endpoint=endpoint)

    def _node_address(self, node: int = 0):
        """ get the ip address from the node for the node index

        We get this information from the list of nodes.  This list of nodes can
        come in various forms, because the primary consumer here is a list of
        nodes from launchpad yaml, and there is variation in that syntax.
        It's not great coding, but we allow for variability here to handle
        differing incoming formats.

        """
        node = self.hosts[node]
        if 'address' in node:
            return node['address']
        elif 'ssh' in node:
            return node['ssh']['address']
        elif 'winrm' in node:
            return node['winrm']['address']
