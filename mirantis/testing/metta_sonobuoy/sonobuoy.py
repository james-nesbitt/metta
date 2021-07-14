"""

Run a Sonobuoy run on a k82 client.

Use this to run the sonobuoy implementation

"""
from typing import Dict, Any, List
import logging
import subprocess
import os
import json
import shutil
from enum import Enum, unique

import yaml
import kubernetes

from mirantis.testing.metta_kubernetes.kubeapi_client import KubernetesApiClientPlugin

logger = logging.getLogger("sonobuoy")

SONODBUOY_DEFAULT_WAIT_PERIOD_SECS = 1440
""" Default time for sonobuoy to wait when running """
SONOBUOY_DEFAULT_BIN = "sonobuoy"
""" Default Bin Name for running sonobuoy """
SONOBUOY_DEFAULT_RESULTS_PATH = "./results"
""" Default path for where to download sonobuoy results """
SONOBUOY_NAMESPACE = "sonobuoy"
"""K8s namespace where sonobuoy puts its stuff (RO)."""

SONOBUOY_CRB_NAME = "sonobuoy-serviceaccount-cluster-admin"
"""Sonobuoy cluster-role-binding name."""
SONOBUOY_CRB_ROLEREF_KIND = "ClusterRole"
"""Sonobuoy cluster-role-binding kind."""
SONOBUOY_CRB_ROLEREF_NAME = "cluster-admin"
"""Sonobuoy cluster-role-binding role."""
SONOBUOY_CRB_SUBJECTS_SERVICEACCOUNT = "sonobuoy-serviceaccount"
"""Sonobuoy cluster-role-binding serviceaccount name."""


# pylint: disable=too-many-instance-attributes
class Sonobuoy:
    """A sonobuoy handler."""

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        api_client: KubernetesApiClientPlugin,
        mode: str,
        kubernetes_version: str = "",
        plugins: List[str] = None,
        plugin_envs: List[str] = None,
        binary: str = SONOBUOY_DEFAULT_BIN,
        results_path: str = SONOBUOY_DEFAULT_RESULTS_PATH,
    ):
        """Initialize the workload instance."""
        self._api_client = api_client
        """Metta api client plugin for kubeconfig and CRB management."""
        self.kubeconfig = api_client.config_file
        """ metta kube client, which gives us a kubeconfig """
        self.mode = mode
        """ sonobuoy mode, passed to the cli """
        self.kubernetes_version = kubernetes_version
        """ Kubernetes version to test compare against """
        self.plugins = plugins if plugins is not None else []
        """ which sonobuoy plugins to run """
        self.plugin_envs = plugin_envs if plugin_envs is not None else []
        """ Plugin specific ENVs to pass to sonobuoy """

        if shutil.which(binary) is None:
            raise ValueError(
                f"Sonobuoy binary not found. Sonobuoy commands cannot be called.  Expected binary at path {binary}"
            )

        self.bin = binary
        """ path to the sonobuoy binary """

        self.results_path = os.path.realpath(results_path)
        """ path to where to download sonobuoy results """

    def run(self, wait: bool = True):
        """Run sonobuoy."""
        cmd = ["run"]
        # we don't need to add --kubeconfig here as self._run() does that

        if self.mode:
            cmd += [f"--mode={self.mode}"]

        if self.kubernetes_version:
            cmd += [f"--kube-conformance-image-version={self.kubernetes_version}"]

        if self.plugins:
            cmd += [f"--plugin={plugin_id}" for plugin_id in self.plugins]

        if self.plugin_envs:
            cmd += [f"--plugin-env={plugin_env}" for plugin_env in self.plugin_envs]

        if wait:
            cmd += [f"--wait={SONODBUOY_DEFAULT_WAIT_PERIOD_SECS}"]

        try:
            logger.info("Ensuring that we have needed K8s CRBs")
            self._create_k8s_crb()
            logger.info("Starting Sonobuoy run : %s", cmd)
            self._run(cmd)
        except subprocess.CalledProcessError as err:
            raise RuntimeError("Sonobuoy RUN failed") from err

    def status(self) -> "SonobuoyStatus":
        """Retrieve Sonobuoy status return."""
        cmd = ["status", "--json"]
        status = self._run(cmd, return_output=True)
        if status:
            return SonobuoyStatus(status)

        return None

    def logs(self, follow: bool = True):
        """Output sonobuoy logs."""
        cmd = ["logs"]

        if follow:
            cmd += ["--follow"]

        self._run(cmd)

    def retrieve(self) -> "SonobuoyResults":
        """Retrieve sonobuoy results."""
        logger.debug("retrieving sonobuoy results to %s", self.results_path)
        try:
            os.makedirs(self.results_path, exist_ok=True)
            cmd = ["retrieve", self.results_path]
            file = self._run(cmd=cmd, return_output=True).rstrip("\n")
            if not os.path.isfile(file):
                raise RuntimeError("Sonobuoy did not retrieve a results tarball.")
            return SonobuoyResults(tarball=file, folder=self.results_path)
        except Exception as err:
            raise RuntimeError("Could not retrieve sonobuoy results") from err

    def destroy(self, wait: bool = False):
        """Delete sonobuoy resources."""
        cmd = ["delete"]

        if wait:
            cmd += ["--wait"]

        self._run(cmd)
        self._delete_k8s_crb()

    def _run(
        self, cmd: List[str], ignore_errors: bool = True, return_output: bool = False
    ):
        """Run a sonobuoy command."""
        cmd = [self.bin, f"--kubeconfig={self.kubeconfig}"] + cmd

        # this else makes it much more readable
        # pylint: disable=no-else-return
        if return_output:
            logger.debug(
                "running sonobuoy command with output capture: %s", " ".join(cmd)
            )
            res = subprocess.run(cmd, shell=False, check=True, stdout=subprocess.PIPE)

            # sonobuoy's uses of subprocess error is overly inclusive for us
            if not ignore_errors:
                res.check_returncode()

            return res.stdout.decode("utf-8")

        else:
            logger.debug("running sonobuoy command: %s", " ".join(cmd))
            res = subprocess.run(cmd, check=True, text=True)

            if not ignore_errors:
                res.check_returncode()

            return res

    def _create_k8s_crb(self):
        """Create the cluster role binding that sonobuoy needs."""
        rbac_authorization_v1_api = self._api_client.get_api("RbacAuthorizationV1Api")

        # if the CRB does not exist then create it.
        try:
            return rbac_authorization_v1_api.read_cluster_role_binding(
                name=SONOBUOY_CRB_NAME
            )
        except kubernetes.client.exceptions.ApiException:
            logger.debug("Sonobuoy CRB not found. Creating it now.")
            body = kubernetes.client.V1ClusterRoleBinding(
                metadata=kubernetes.client.V1ObjectMeta(
                    name=SONOBUOY_CRB_NAME,
                ),
                subjects=[
                    kubernetes.client.V1Subject(
                        kind="ServiceAccount",
                        name=SONOBUOY_CRB_SUBJECTS_SERVICEACCOUNT,
                        namespace="sonobuoy",
                    )
                ],
                role_ref=kubernetes.client.V1RoleRef(
                    kind=SONOBUOY_CRB_ROLEREF_KIND,
                    name=SONOBUOY_CRB_ROLEREF_NAME,
                    api_group="rbac.authorization.k8s.io",
                ),
            )

            try:
                return rbac_authorization_v1_api.create_cluster_role_binding(
                    body=body
                )
            except kubernetes.client.exceptions.ApiException as err:
                raise RuntimeError(
                    "Sonobuoy could not create the needed K8s CRB."
                ) from err

    def _delete_k8s_crb(self):
        """Remove the cluster role binding that we created."""
        rbac_authorization_v1_api = self._api_client.get_api("RbacAuthorizationV1Api")

        try:
            return rbac_authorization_v1_api.delete_cluster_role_binding(name=SONOBUOY_CRB_NAME)
            logger.debug("Sonobuoy CRB found.")
        except kubernetes.client.exceptions.ApiException as err:
            logger.error("Could not delete sonobuoy CRB: %s", err)


class SonobuoyStatus:
    """A status output from the sonobuoy CLI."""

    def __init__(self, status_json: str):
        """Build from sonobuoy status results."""
        status = json.loads(status_json)
        self.status = Status(status["status"])
        self.tar_info = status["tar-info"]

        self.plugins = {}
        for plugin in status["plugins"]:
            self.plugins[plugin["plugin"]] = plugin

    def plugin_list(self):
        """Retrieve the list of plugins."""
        return list(self.plugins.keys())

    def plugin(self, plugin: str):
        """Retrieve the results for one plugin."""
        return self.plugins[plugin]

    def plugin_status(self, plugin: str) -> "Status":
        """Get the status code for a plugin."""
        status_string = self.plugin(plugin)["status"]
        return Status(status_string)

    def __str__(self) -> str:
        """Convert to a string."""
        status: List[str] = []
        for plugin_id in self.plugin_list():
            status.append(f"{plugin_id}:{self.plugin_status(plugin_id)}")
        return f"[{']['.join(status)}]"


class SonobuoyResults:
    """Results retrieved analyzer."""

    def __init__(self, tarball: str, folder: str):
        """Interpret tarball contents."""
        logger.debug("un-tarring retrieved results: %s", tarball)
        res = subprocess.run(
            ["tar", "-xzf", tarball, "-C", folder], check=True, text=True
        )
        res.check_returncode()

        self.results_path = folder

        with open(os.path.join(folder, "meta", "config.json")) as config_json:
            self.meta_config = json.load(config_json)
        with open(os.path.join(folder, "meta", "info.json")) as info_json:
            self.meta_info = json.load(info_json)
        with open(os.path.join(folder, "meta", "query-time.json")) as qt_json:
            self.meta_querytime = json.load(qt_json)

        self.plugins = []
        for plugin_id in self.meta_info["plugins"]:
            self.plugins.append(plugin_id)

    def plugin_list(self):
        """Return a string list of plugin ids."""
        return self.plugins

    def plugin(self, plugin_id) -> "SonobuoyResultsPlugin":
        """Return the results for a single plugin."""
        return SonobuoyResultsPlugin(
            os.path.join(self.results_path, "plugins", plugin_id)
        )


class SonobuoyResultsPlugin:
    """The full results for a plugin."""

    def __init__(self, path: str):
        """Load results for a plugin results call."""
        with open(os.path.join(path, "sonobuoy_results.yaml")) as results_yaml:
            self.summary = yaml.safe_load(results_yaml)

    def name(self) -> str:
        """Return string name of plugin."""
        return self.summary["name"]

    def status(self) -> "Status":
        """Return the status object for the plugin results."""
        return Status(self.summary["status"])

    def __len__(self):
        """Count how many items are in the plugin_results."""
        return len(self.summary["items"])

    def __getitem__(self, instance_id: Any) -> "SonobuoyResultsPluginItem":
        """Get item details from the plugin results."""
        return SonobuoyResultsPluginItem(item_dict=self.summary["items"][instance_id])


class SonobuoyResultsPluginItem:
    """An individual item from a sonobuoy results plugin."""

    def __init__(self, item_dict: Dict[str, Any]):
        """Single plugin result item."""
        self.name = item_dict["name"]
        self.status = Status(item_dict["status"])
        self.meta = item_dict["meta"]
        self.details = item_dict["details"] if "details" in item_dict else {}

    def meta_file_path(self):
        """Get the path to the error item file."""
        return self.meta["file"]

    def meta_file(self):
        """Get the contents of the file."""
        with open(self.meta_file_path()) as meta_file:
            return yaml.safe_load(meta_file)


@unique
class Status(Enum):
    """Enumerator to plugin states."""

    PENDING = "pending"
    """ still pending """
    RUNNING = "running"
    """ testing is running """
    FAILED = "failed"
    """ testing has failed """
    COMPLETE = "complete"
    """ testing has completed without failure """
    PASSED = "passed"
    """ testing has passed """
    POSTPROCESS = "post-processing"
    """ testing has finished and is being processed """
