"""

Mirantis MSR API interaction.

Two Metta plugins:

1. The Metta cli plugin allows CLI interaction with MSR client plugin
   from the command line tool.
2. The Metta client plugin allows interaction with the MSR API.

"""

import logging
import json
from typing import List, Dict
from enum import Enum

import requests

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.fixtures import Fixtures
from mirantis.testing.metta.healthcheck import Health, HealthStatus

logger = logging.getLogger("metta.contrib.metta_mirantis.client.msrapi")


METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID = "mirantis_msr_client"
""" Mirantis MSR APIP Client plugin id """


class MSRReplicaHealth(Enum):
    """MSR replica health values (in the cluster status API response)."""

    OK = "OK"

    def match(self, compare: str) -> bool:
        """Allow for string comparisons."""
        # pylint: disable=comparison-with-callable
        return self.value == compare


# pylint: disable=too-many-instance-attributes
class MSRAPIClientPlugin:
    """Client for API Connections to MSR."""

    # pylint: disable=too-many-arguments"
    def __init__(
        self,
        environment: Environment,
        instance_id: str,
        accesspoint: str,
        username: str,
        password: str,
        hosts: List[Dict],
        api_version: str = "v0",
        protocol: str = "https",
    ):
        """Create new MSR Client API plugin.

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
            The first node in the list is used as an API endpoint if no
            endpoint is specified.

        """
        self._environment = environment
        """ Environemnt in which this plugin exists."""
        self._instance_id = instance_id
        """ Unique id for this plugin instance."""

        self.accesspoint = accesspoint
        self.username = username
        self.password = password

        self.hosts = hosts if hosts else []
        """ List of hosts """

        self.protocol = protocol
        """What procotol should be used with the endpoint (http/https.)"""

        if not self.accesspoint:
            # use the first host as an accesspoint if none was delivered
            self.accesspoint = self._node_address(0)

        self.version = api_version
        """ used to build the api url """

        self.verify = False
        """ should we verify ssl certs : default to NO """
        if not self.verify:
            # pylint: disable=no-member
            requests.packages.urllib3.disable_warnings(
                requests.packages.urllib3.exceptions.InsecureRequestWarning
            )

        self.auth_token = None
        """ hold the bearer auth token if created by ._auth_headers() """

        self.fixtures = Fixtures()
        """fixtures created by this plugin."""

    def host_count(self):
        """Return integer host count for MSR cluster."""
        return len(self.hosts)

    def info(self, deep: bool = False):
        """Return information about the plugin."""
        info = {
            "api": {
                "accesspoint": self.accesspoint,
                "username": self.username,
            },
            "hosts": self.hosts,
        }

        if deep:
            info["version"] = self.api_version()
            info["features"] = self.api_features()
            info["status"] = self.api_status()

        return info

    def health(self) -> Health:
        """Determine the health of the MSR instance."""
        msr_health = Health(source=self._instance_id, status=HealthStatus.UNKNOWN)

        for _health_health_function in [
            self._health_node_health,
            self._health_msr_replica_health,
            self._health_msr_alerts,
        ]:
            _health_health = _health_health_function()
            msr_health.merge(_health_health)

        return msr_health

    def api_ping(self, node: int = None) -> bool:
        """Check the API ping response."""
        endpoint = self._accesspoint_url("_ping", root_api=True, node=node)

        with requests.get(endpoint, verify=self.verify) as response:
            response.raise_for_status()
            return response.ok

    def api_health(self, node: int = None):
        """Check the API ping response."""
        endpoint = self._accesspoint_url("health", root_api=True, node=node)

        with requests.get(
            endpoint, auth=self._api_auth(), verify=self.verify
        ) as response:
            response.raise_for_status()
            return json.loads(response.content)

    def api_nginx_status(self, node: int = None):
        """Check the API ping response.

        Returns:
        --------
        parsed string contents of the response

        """
        endpoint = self._accesspoint_url("nginx_status", root_api=True, node=node)

        with requests.get(
            endpoint,
            auth=self._api_auth(),
            headers={"content-type": "application/json"},
            verify=self.verify,
        ) as response:
            response.raise_for_status()
            # @TODO should we parse this?
            return response.content.decode("utf-8")

    def api_version(self) -> Dict:
        """Retrieve version."""
        with requests.get(
            self._accesspoint_url("admin/version"),
            auth=self._api_auth(),
            verify=self.verify,
        ) as response:
            response.raise_for_status()
            return json.loads(response.content)

    def api_status(self) -> Dict:
        """Retrieve status from the api."""
        with requests.get(
            self._accesspoint_url("meta/cluster_status"),
            auth=self._api_auth(),
            verify=self.verify,
        ) as response:
            response.raise_for_status()
            return json.loads(response.content)

    def api_features(self) -> Dict:
        """Retrieve features list from the api."""
        with requests.get(
            self._accesspoint_url("meta/features"),
            auth=self._api_auth(),
            verify=self.verify,
        ) as response:
            response.raise_for_status()
            return json.loads(response.content)

    def api_alerts(self) -> Dict:
        """Retrieve alerts list from the api."""
        with requests.get(
            self._accesspoint_url("meta/alerts"),
            auth=self._api_auth(),
            verify=self.verify,
        ) as response:
            response.raise_for_status()
            return json.loads(response.content)

    def _api_auth(self):
        """Get the requests auth handler."""
        return requests.auth.HTTPBasicAuth(self.username, self.password)

    def _accesspoint_url(
        self, endpoint: str = "", root_api: bool = False, node: int = None
    ) -> str:
        """Convert an endpoint into a full URL for an API Call.

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

        Returns:
        --------
        String URL for API endpoint

        """
        if node is None:
            target = self.accesspoint
        else:
            target = self._node_address(node)

        if root_api:
            return f"{self.protocol}://{target}/{endpoint}"

        return f"{self.protocol}://{target}/api/{self.version}/{endpoint}"

    def _node_address(self, node: int = 0) -> str:
        """Get the ip address from the node for the node index.

        We get this information from the list of nodes.  This list of nodes can
        come in various forms, because the primary consumer here is a list of
        nodes from launchpad yaml, and there is variation in that syntax.
        It's not great coding, but we allow for variability here to handle
        differing incoming formats.

        Returns:
        --------
        String node address

        """
        node_dict = self.hosts[node]
        if "address" in node_dict:
            return node_dict["address"]
        if "ssh" in node_dict:
            return node_dict["ssh"]["address"]
        if "winrm" in node_dict:
            return node_dict["winrm"]["address"]

        raise ValueError(f"No node address could be found for the node {node}")

    def _health_node_health(self):
        """Test node health."""
        health = Health(source=self._instance_id)

        for node_index in range(self.host_count()):
            node_health = self.api_health(node=node_index)
            if node_health["Healthy"]:
                health.info(f"MSR: Node [{node_index}] is healthy")
            else:
                health.error(node_health["Error"])

        return health

    def _health_msr_replica_health(self):
        """Test that we can access node information."""
        health = Health(source=self._instance_id)

        status = self.api_status()
        replica_health = status["replica_health"]

        if replica_health is None:
            health.warning(
                "MSR: cluster reports a null replica health. This occurs for MSR on K8s."
            )
        else:
            for replica_id, replica_health in status["replica_health"].items():
                if not MSRReplicaHealth.OK.match(replica_health):
                    health.error(
                        f"MSR: Replica [{replica_id}] is not READY : {replica_health}"
                    )

        return health

    def _health_msr_alerts(self):
        """Confirm that we can get alerts."""
        health = Health(source=self._instance_id)

        alerts = self.api_alerts()

        for alert in alerts:
            health.warning(
                f"MSR: alert: {alert['id']} {alert['class']}: {alert['message']}"
                f" {alert['url'] if hasattr(alert, 'url') else ''}"
            )

        return health
