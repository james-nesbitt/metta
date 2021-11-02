"""

Run a Sonobuoy run on a k82 client.

Use this to run the sonobuoy implementation

"""
from typing import Dict, Any, List
import logging
import subprocess
import os
import shutil
import tempfile

import kubernetes

from mirantis.testing.metta_kubernetes.kubeapi_client import KubernetesApiClientPlugin

from .plugin import Plugin
from .results import SonobuoyResults, SonobuoyStatus

logger = logging.getLogger("sonobuoy")

SONODBUOY_DEFAULT_WAIT_PERIOD_SECS = 1440
""" Default time for sonobuoy to wait when running """
SONODBUOY_DEFAULT_WAIT_OUTPUT = "progress"
"""What type of --wait-ouput to pass to sonobuoy run with --wait."""
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
class SonobuoyClient:
    """A sonobuoy handler."""

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        kubeclient: KubernetesApiClientPlugin,
        plugins: List[Plugin] = None,
        binary: str = SONOBUOY_DEFAULT_BIN,
        results_path: str = SONOBUOY_DEFAULT_RESULTS_PATH,
        create_crbs: bool = True,
    ):
        """Initialize the workload instance."""
        self._api_client = kubeclient
        """Kube API metta client, used for a config file and for creating K8s resources."""
        self.kubeconfig = kubeclient.config_file
        """String path to a kubeconfig file."""

        self.plugins = plugins if plugins is not None else []
        """Which sonobuoy plugins to run."""

        if shutil.which(binary) is None:
            raise ValueError(
                "Sonobuoy binary not found. Sonobuoy commands cannot be called. "
                f"Expected binary at path {binary}"
            )

        self.bin = binary
        """Path to the sonobuoy binary."""

        self.results_path = os.path.realpath(results_path)
        """Path to where to download sonobuoy results."""

        self.create_crbs: bool = create_crbs
        """Whether or not this client should create sonobuoy CRB resources."""

    # deep is a metta info standard and expected to be here
    # pylint: disable=unused-argument
    def info(self, deep: bool = False) -> Dict[str, Any]:
        """Provide a Dict of info about the client."""
        return {
            "config": {
                "kubeconfig": self.kubeconfig,
                "results_path": self.results_path,
            },
            "plugins": [plugin.info(deep=deep) for plugin in self.plugins],
            "client": {
                "sonobuoy_bin_path": self.bin,
            },
        }

    def run(self, wait: bool = True, run_args: List[str] = None):
        """Run sonobuoy."""
        cmd = ["run"]

        if run_args is not None:
            cmd += run_args

        if self.plugins:
            for plugin in self.plugins:
                cmd += plugin.run_args()

        if wait:
            cmd += [f"--wait={SONODBUOY_DEFAULT_WAIT_PERIOD_SECS}"]
            cmd += [f"--wait-output={SONODBUOY_DEFAULT_WAIT_OUTPUT}"]

        try:
            if self.create_crbs:
                logger.info("Ensuring that we have needed K8s CRBs")
                self.create_k8s_crb()
            logger.info("Starting Sonobuoy run : %s", cmd)
            self._run(cmd)
        except subprocess.CalledProcessError as err:
            raise RuntimeError("Sonobuoy RUN failed") from err

    def status(self) -> "SonobuoyStatus":
        """Retrieve Sonobuoy status return."""
        cmd = ["status", "--json"]
        status = self._run(cmd, return_output=True)
        if status is None:
            raise ValueError("Sonobuoy did not return a status.")
        return SonobuoyStatus(status)

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

    def results(self) -> str:
        """Report on sonobuoy results."""
        logger.debug("retrieving sonobuoy results to %s", self.results_path)
        try:
            with tempfile.TemporaryDirectory() as tmpdirname:
                print("created temporary directory", tmpdirname)
                cmd = ["retrieve", tmpdirname]
                file_name = self._run(cmd=cmd, return_output=True).rstrip("\n")
                if not os.path.isfile(file_name):
                    raise RuntimeError("Sonobuoy did not retrieve a results tarball.")
                cmd = ["results", os.path.join(tmpdirname, file_name)]
                return self._run(cmd=cmd, include_kubeconfig=False, return_output=True)
        except Exception as err:
            raise RuntimeError("Could not retrieve sonobuoy results") from err

    # pylint: disable=redefined-builtin
    def delete(self, all: bool = True, wait: bool = False):
        """Delete sonobuoy resources."""
        cmd = ["delete"]

        if wait:
            cmd += ["--wait"]
            cmd += [f"--wait-output={SONODBUOY_DEFAULT_WAIT_OUTPUT}"]

        self._run(cmd)
        if self.create_crbs:
            self.delete_k8s_crb()

    def version(self) -> Dict[str, str]:
        """Retrieve sonobuoy version info."""
        cmd = ["version"]
        version_string = self._run(cmd, return_output=True)
        version: Dict[str, str] = {}
        for version_item_string in version_string.strip().split("\n"):
            version_item_list = version_item_string.split(":")
            key = version_item_list[0].strip()
            value = version_item_list[1].strip()
            version[key] = value
        return version

    def _run(
        self,
        cmd: List[str],
        ignore_errors: bool = True,
        return_output: bool = False,
        include_kubeconfig: bool = True,
    ):
        """Run a sonobuoy command."""
        cmd = [self.bin] + cmd

        if include_kubeconfig:
            cmd += [f"--kubeconfig={self.kubeconfig}"]

        # this else makes it much more readable
        # pylint: disable=no-else-return
        if return_output:
            logger.debug("running sonobuoy command with output capture: %s", " ".join(cmd))
            return_res = subprocess.run(cmd, shell=False, check=True, stdout=subprocess.PIPE)

            # sonobuoy's uses of subprocess error is overly inclusive for us
            if not ignore_errors:
                return_res.check_returncode()

            return return_res.stdout.decode("utf-8")

        else:
            logger.warning("running sonobuoy command: %s", " ".join(cmd))
            res = subprocess.run(cmd, check=True, text=True)

            if not ignore_errors:
                res.check_returncode()

            return res

    def create_k8s_crb(self):
        """Create the cluster role binding that sonobuoy needs."""
        rbac_authorization_v1_api = self._api_client.get_api("RbacAuthorizationV1Api")

        # if the CRB does not exist then create it.
        try:
            return rbac_authorization_v1_api.read_cluster_role_binding(
                name=SONOBUOY_CRB_NAME
            ).to_dict()
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
                    kind="ClusterRole",
                    name=SONOBUOY_CRB_ROLEREF_NAME,
                    api_group="rbac.authorization.k8s.io",
                ),
            )

            try:
                return rbac_authorization_v1_api.create_cluster_role_binding(body=body)
            except kubernetes.client.exceptions.ApiException as err:
                raise RuntimeError("Sonobuoy could not create the needed K8s CRB.") from err

    def delete_k8s_crb(self):
        """Remove the cluster role binding that we created."""
        rbac_authorization_v1_api = self._api_client.get_api("RbacAuthorizationV1Api")

        try:
            return rbac_authorization_v1_api.delete_cluster_role_binding(
                name=SONOBUOY_CRB_NAME
            ).to_dict()
        except kubernetes.client.exceptions.ApiException as err:
            logger.error("Could not delete sonobuoy CRB: %s", err)
            return None
