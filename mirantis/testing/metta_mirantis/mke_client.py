"""

Mirantis MKE API interaction.

Two Metta plugins:

1. The Metta cli plugin allows CLI interaction with MKE client plugin
   from the command line tool.
2. The Metta client plugin allows interaction with the MKE API.

"""

import logging
import json
import os
import pathlib
import shutil
import datetime
from typing import Dict, List
from enum import Enum

import zipfile
import requests
import toml

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta_health.healthcheck import Health, HealthStatus
from mirantis.testing.metta.fixture import Fixtures
from mirantis.testing.metta_docker import METTA_PLUGIN_ID_DOCKER_CLIENT
from mirantis.testing.metta_kubernetes import METTA_PLUGIN_ID_KUBERNETES_CLIENT

logger = logging.getLogger("metta.contrib.metta_mirantis.client.mkeapi")

METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID = "mirantis_mke_client"
""" Mirantis MKE API Client plugin id """

METTA_MIRANTIS_MKE_BUNDLE_PATH_DEFAULT = "."
""" Default path to be used as a root dir for client bundles """
METTA_MIRANTIS_MKE_BUNDLE_ZIP_FILENAME = "mke_bundle.zip"
""" Default filename for downloaded client bundle zip file """
METTA_MIRANTIS_MKE_BUNDLE_INFO_FILENAME = "meta.json"
""" Filename in the bundle which contains the bundle metadata. """

METTA_MIRANTIS_MKE_DOCKER_VERSION_DEFAULT = "1.40"
""" Default value for the docker client version number."""


class MKENodeState(Enum):
    """MKE Node state in the node status API response."""

    UNKNOWN = "unknown"
    DOWN = "down"
    READY = "ready"
    DISCONNECTED = "disconnected"

    # pylint: disable=comparison-with-callable
    def match(self, compare: str) -> bool:
        """Allow for string comparisons."""
        return self.value == compare


# pylint: disable=too-many-instance-attributes, too-many-public-methods
class MKEAPIClientPlugin:
    """Metta Client plugin for API Connections to MKE."""

    # pylint: disable=too-many-arguments"
    def __init__(
        self,
        environment: Environment,
        instance_id: str,
        accesspoint: str,
        username: str,
        password: str,
        hosts: List[Dict],
        bundle_root: str = METTA_MIRANTIS_MKE_BUNDLE_PATH_DEFAULT,
    ):
        """Create an MKE Client plugin instance.

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

        bundle_root (str) : string path to the root folder where this
            client should store any downloaded client bundles. The string
            path will be created if missing, and then any downlaoaded client
            bundle will be put into a subfolder based on the username.

        """
        self._environment: Environment = environment
        """ Environemnt in which this plugin exists """
        self._instance_id: str = instance_id
        """ Unique id for this plugin instance """

        self.accesspoint: str = accesspoint
        self.username: str = username
        self.password: str = password

        self.hosts: List[Dict] = hosts
        """ List of hosts """

        self._bundle_root: str = bundle_root
        """ String path which should be used as a root path for storing client
           bundles """

        if not self.accesspoint:
            # use the first host as an accesspoint if none was delivered
            self.accesspoint = self._node_address(0)

        self.verify: bool = False
        """ should we verify ssl certs """
        if not self.verify:
            # pylint: disable=no-member
            requests.packages.urllib3.disable_warnings(
                requests.packages.urllib3.exceptions.InsecureRequestWarning
            )

        self.auth_token: str = None
        """ hold the bearer auth token created by ._auth_headers() (cache) """

        self._timeout = 10.00
        """Python requests timeout to use."""

        self.fixtures = Fixtures()
        """ This plugin keeps fixtures """

        # If we can ping one of the hosts then let's try to retrieve a client
        # bundle.  If we can get a client bundle, then we can add docker
        # and kubectl_api client clients to the fixtures stack for the env.
        # We will broadly ignore exceptions as we are optimistically hoping
        # that we are even installed at this point.
        # self.make_fixtures()
        try:
            self.make_fixtures()
        except ValueError as err:
            logger.debug("MKE client was unable to create clients: %s", err)

    def host_count(self):
        """Return integer host count for MKE cluster."""
        return len(self.hosts)

    def info(self, deep: bool = False):
        """Return information about the plugin."""
        info = {
            "api": {
                "accesspoint": self.accesspoint,
                "username": self.username,
            },
            "bundle_root": self._bundle_root,
            "hosts": self.hosts,
        }

        if deep:
            info["id"] = self.api_id()
            info["version"] = self.api_version()
            info["api_info"] = self.api_info()

        return info

    def health(self) -> Health:
        """Determine the health of the MKE instance."""
        mke_health = Health(source=self._instance_id, status=HealthStatus.UNKNOWN)

        for test_health_function in [
            self._health_self_mke_api_id,
            self._health_mke_nodes,
            self._health_mke_swarminfo,
        ]:
            test_health = test_health_function()
            mke_health.merge(test_health)

        return mke_health

    def auth_header(self) -> Dict:
        """Retrieve the auth headers so you can do your own thing."""
        return json.loads(self._auth_headers())

    def api_ping(self, node: int = None) -> bool:
        """Check the API ping response."""
        if node is not None:
            endpoint = self._accesspoint_url("_ping", node=node)
        else:
            endpoint = self._accesspoint_url("_ping")

        with requests.get(endpoint, verify=self.verify, timeout=self._timeout) as response:
            response.raise_for_status()
            return response.ok

    def api_id(self) -> Dict:
        """Retrieve the API id."""
        with requests.get(
            self._accesspoint_url("id"),
            headers=self._auth_headers(),
            verify=self.verify,
            timeout=self._timeout,
        ) as response:
            response.raise_for_status()
            return json.loads(response.content)

    def api_version(self) -> Dict:
        """Retrieve version."""
        with requests.get(
            self._accesspoint_url("version"),
            headers=self._auth_headers(),
            verify=self.verify,
            timeout=self._timeout,
        ) as response:
            response.raise_for_status()
            return json.loads(response.content)

    def api_info(self) -> Dict:
        """Retrieve the API info."""
        with requests.get(
            self._accesspoint_url("info"),
            headers=self._auth_headers(),
            verify=self.verify,
            timeout=self._timeout,
        ) as response:
            response.raise_for_status()
            return json.loads(response.content)

    def api_logs(self):
        """Retrieve config toml as a struct."""
        endpoint = "logs"
        with requests.get(
            self._accesspoint_url(endpoint),
            headers=self._auth_headers(),
            verify=self.verify,
            timeout=self._timeout,
        ) as response:
            response.raise_for_status()
            return response.text

    def api_logs_path(self, path: str):
        """Retrieve config toml as a struct."""
        endpoint = f"logs/{path}"
        with requests.get(
            self._accesspoint_url(endpoint),
            headers=self._auth_headers(),
            verify=self.verify,
            timeout=self._timeout,
        ) as response:
            response.raise_for_status()
            return response.text

    def api_nodes(self, node_id: str = "") -> Dict:
        """Retrieve the API nodes."""
        endpoint = f"nodes/{node_id}" if node_id else "nodes"
        with requests.get(
            self._accesspoint_url(endpoint),
            headers=self._auth_headers(),
            verify=self.verify,
            timeout=self._timeout,
        ) as response:
            response.raise_for_status()
            return json.loads(response.content)

    def api_services(self, service_id: str = "") -> Dict:
        """Retrieve the API services."""
        endpoint = f"services/{service_id}" if service_id else "services"
        with requests.get(
            self._accesspoint_url(endpoint),
            headers=self._auth_headers(),
            verify=self.verify,
            timeout=self._timeout,
        ) as response:
            response.raise_for_status()
            return json.loads(response.content)

    def api_metrics_discovery(self):
        """Retrieve the API metrics."""
        endpoint = "metricsdiscovery"
        with requests.get(
            self._accesspoint_url(endpoint),
            headers=self._auth_headers(),
            verify=self.verify,
            timeout=self._timeout,
        ) as response:
            response.raise_for_status()
            return json.loads(response.content)

    def api_tasks(self):
        """Retrieve the API tasks."""
        endpoint = "tasks"
        with requests.get(
            self._accesspoint_url(endpoint),
            headers=self._auth_headers(),
            verify=self.verify,
            timeout=self._timeout,
        ) as response:
            response.raise_for_status()
            return json.loads(response.content)

    def api_task(self, task_id: str):
        """Retrieve the API tasks."""
        endpoint = f"tasks/{task_id}"
        with requests.get(
            self._accesspoint_url(endpoint),
            headers=self._auth_headers(),
            verify=self.verify,
            timeout=self._timeout,
        ) as response:
            response.raise_for_status()
            return json.loads(response.content)

    def api_ucp_configtoml_get(self):
        """Retrieve config toml as a struct."""
        endpoint = "api/ucp/config-toml"
        with requests.get(
            self._accesspoint_url(endpoint),
            headers=self._auth_headers(),
            verify=self.verify,
            timeout=self._timeout,
        ) as response:
            response.raise_for_status()
            return toml.loads(response.text)

    def api_ucp_configtoml_put(self, data):
        """Send struct config as a toml string."""
        endpoint = "api/ucp/config-toml"
        data_toml = toml.dumps(data)
        with requests.put(
            self._accesspoint_url(endpoint),
            headers=self._auth_headers(),
            verify=self.verify,
            timeout=self._timeout,
            data=data_toml,
        ) as response:
            response.raise_for_status()
            return {"response": json.loads(response.content), "data": data}

    def api_get_bundle(self, force: bool = True):
        """Download and extract client bundle to path."""
        endpoint: str = "api/clientbundle"

        # Path in which we should put the client bundle for this user
        bundle_dir: str = self._bundle_user_path()
        # Path to the zip file we will download
        bundle_zip_file: str = os.path.join(bundle_dir, METTA_MIRANTIS_MKE_BUNDLE_ZIP_FILENAME)

        if (not force) and os.path.isdir(bundle_dir):
            return

        logger.info("MKE client downloading client bundle for %s", self.username)
        with requests.get(
            self._accesspoint_url(endpoint),
            headers=self._auth_headers(),
            verify=self.verify,
            timeout=self._timeout,
        ) as response:
            response.raise_for_status()

            if os.path.isdir(bundle_dir):
                shutil.rmtree(bundle_dir)
            pathlib.Path(bundle_dir).mkdir(parents=True, exist_ok=True)

            with open(bundle_zip_file, "wb") as bundle_zip:
                bundle_zip.write(response.content)

        with zipfile.ZipFile(bundle_zip_file) as zipfile_object:
            zipfile_object.extractall(path=bundle_dir)
            os.unlink(bundle_zip_file)

        # now we instruct to rebuild the fixture list.
        self.make_fixtures()

    def api_read_bundle_meta(self):
        """Parse and return the client bundle metadata."""
        # Path to the client bundle metadata file.
        client_bundle_meta_file: str = os.path.join(
            self._bundle_user_path(), METTA_MIRANTIS_MKE_BUNDLE_INFO_FILENAME
        )
        # Path in which we should put the client bundle for this user
        bundle_dir: str = self._bundle_user_path()

        # Will hold data pulled from the client meta data file
        data = {}
        try:
            with open(client_bundle_meta_file) as json_file:
                data = json.load(json_file)

                # helm complains if this file has loose permissions
                client_bundle_kubeconfig_file = os.path.join(bundle_dir, "kube.yml")
                os.chmod(client_bundle_kubeconfig_file, 0o600)
        except FileNotFoundError as err:
            raise ValueError(
                f"failed to open the launchpad client bundle meta "
                f"file : {client_bundle_meta_file}"
            ) from err

        # Not sure why this isn't in there:
        data["Endpoints"]["kubernetes"]["kubeconfig"] = client_bundle_kubeconfig_file
        # add some stuff that a client bundle always has
        data["path"] = bundle_dir
        data["modified"] = datetime.datetime.fromtimestamp(
            os.path.getmtime(client_bundle_meta_file)
        ).strftime("%Y-%m-%d %H:%M:%S")
        # this stuff should already be in the bundle, but it isn't
        data["tls_paths"] = {
            "docker": os.path.join(bundle_dir, "tls", "docker"),
            "kubernetes": os.path.join(bundle_dir, "tls", "kubernetes"),
        }

        return data

    def make_fixtures(self):
        """Make metta clients from the client bundle."""
        bundle_info = self.api_read_bundle_meta()

        # KUBE Client

        kube_config = os.path.join(bundle_info["path"], "kube.yml")
        if os.path.exists(kube_config):
            instance_id = f"{self._instance_id}-{METTA_PLUGIN_ID_KUBERNETES_CLIENT}"
            fixture = self._environment.new_fixture(
                plugin_id=METTA_PLUGIN_ID_KUBERNETES_CLIENT,
                instance_id=instance_id,
                priority=70,
                arguments={"kube_config_file": kube_config},
                labels={
                    "parent_plugin_id": METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID,
                    "parent_instance_id": self._instance_id,
                },
                replace_existing=True,
            )
            # use the parent UCCTFixturesPlugin methods for adding fixtures
            self.fixtures.add(fixture, replace_existing=True)

        # DOCKER CLIENT
        #
        # @NOTE we pass in a docker API constraint because I ran into a case where the
        #   client failed because the python library was ahead in API version

        try:
            host = bundle_info["Endpoints"]["docker"]["Host"]
            cert_path = bundle_info["tls_paths"]["docker"]
        except TypeError as err:
            logger.error(
                "Could not read client bundle properly: %s",
                bundle_info["Endpoints"]["docker"]["Host"],
            )
            raise err

        instance_id = f"{self._instance_id}-{METTA_PLUGIN_ID_DOCKER_CLIENT}"
        fixture = self._environment.new_fixture(
            plugin_id=METTA_PLUGIN_ID_DOCKER_CLIENT,
            instance_id=instance_id,
            priority=70,
            arguments={
                "host": host,
                "cert_path": cert_path,
                "version": METTA_MIRANTIS_MKE_DOCKER_VERSION_DEFAULT,
            },
            labels={
                "parent_plugin_id": METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID,
                "parent_instance_id": self._instance_id,
            },
            replace_existing=True,
        )
        # use the parent UCCTFixturesPlugin methods for adding fixtures
        self.fixtures.add(fixture, replace_existing=True)

    def rm_bundle(self):
        """Remove any downloaded client bundles."""
        bundle_dir = self._bundle_user_path()

        if not os.path.isdir(bundle_dir):
            logger.warning("MKE Client was asked to delete client bundle, but we don't have one.")
            return None

        return shutil.rmtree(bundle_dir)

    def _bundle_user_path(self):
        """Build a string path to where the user client bundle should be put."""
        return f"{self._bundle_root}.{self.username}"

    def _auth_headers(self):
        """Get an auth token."""
        if self.auth_token is None:
            data = {"password": self.password, "username": self.username}
            with requests.post(
                self._accesspoint_url("auth/login"),
                data=json.dumps(data),
                verify=self.verify,
                timeout=self._timeout,
            ) as response:
                response.raise_for_status()
                content = json.loads(response.content)
                self.auth_token = content["auth_token"]

        return {"Authorization": f"Bearer {self.auth_token}"}

    def _accesspoint_url(self, endpoint: str = "", node: int = None):
        """Convert an endpoint into a full URL for an API Call.

        Pass in a sub-url endpoint and this will convert it into a full URL.
        You can request a specific host index if desired.

        Parameters:
        -----------
        endpoint (str) : API endpoint you are trying to access

        node (int) : If not None, then the API call should be directed to a
            specific node index from the list of hosts, as opposed to the
            generic accesspoint. This allows things like ping confirmation on
            specific host.

        """
        if node is None:
            target = self.accesspoint
        else:
            target = self._node_address(node)

        return f"https://{target.rstrip('/')}/{endpoint.lstrip('/')}"

    def _node_address(self, node: int = 0):
        """Get the ip address from the node for the node index."""
        node_dict = self.hosts[node]
        if "mke_accesspoint" in node_dict:
            return node_dict["mke_accesspoint"]
        if "address" in node_dict:
            return node_dict["address"]
        if "public_ip" in node_dict:
            return node_dict["public_ip"]
        if "ssh" in node_dict:
            return node_dict["ssh"]["address"]
        if "winrm" in node_dict:
            return node_dict["winrm"]["address"]

        raise ValueError(f"No node address could be found for the node {node}")

    def _health_self_mke_api_id(self):
        """Did we get a good mke client."""
        health = Health(source=self._instance_id)

        info = self.api_info()

        health.info(f"MKE:API: Cluster: ID: {info['ID']}")

        if hasattr(info, "Warnings") and len(info["Warnings"]) > 0:
            for warning in info["Warnings"]:
                health.warning(f"MKE:API: Warning : {warning}")
        else:
            health.healthy("MKE:API: reports no warnings.")

        return health

    def _health_mke_nodes(self):
        """Confirm that we get a good mke client."""
        health = Health(source=self._instance_id)

        nodes = self.api_nodes()

        all_healthy = True
        for node in nodes:
            if MKENodeState.READY.match(node["Status"]["State"]):
                health.healthy(f"MKE:Node: {node['ID']} : {node['Status']['Message']}")
            else:
                health.warning(f"MKE:Node: {node['ID']} : {node['Status']['Message']}")
                all_healthy = False

        if all_healthy:
            health.healthy("MKE:Nodes: reports all nodes are healthy.")

        return health

    def _health_mke_swarminfo(self):
        """Confirm that we get a good mke client."""
        health = Health(source=self._instance_id)

        info = self.api_info()

        if "Swarm" in info:
            swarm_info = info["Swarm"]

            # @NOTE there is a lot of info in this Dict, but it isn't clear
            #    what of that information is actually usefull.

            if swarm_info["Error"] == 0:
                swarm_error = swarm_info["Error"]
                health.errorf(f"MKE:swarm: {swarm_error}")
            if swarm_info["Nodes"] == 0:
                health.error("MKE:Nodes: reports no nodes in the cluster")

        if info["Warnings"]:
            warnings = info["Warnings"]
            health.warning(f"MKE:Warning: {warnings}")

        return health
