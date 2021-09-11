"""

Helm workload Metta plugin

As a workload, using a kube_api client, manage helm charts

"""
from typing import Any, List, Dict
import logging
import subprocess
import shutil
from enum import Enum

import yaml

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.fixture import Fixtures
from mirantis.testing.metta.client import METTA_PLUGIN_INTERFACE_ROLE_CLIENT
from mirantis.testing.metta_health.healthcheck import Health

from .kubeapi_client import METTA_PLUGIN_ID_KUBERNETES_CLIENT

logger = logging.getLogger("metta.contrib.kubernetes.workload.helm")

METTA_PLUGIN_ID_KUBERNETES_HELM_WORKLOAD = "metta_kubernetes_helm_workload"
""" workload plugin_id for the metta_kubernetes helm plugin """


KUBERNETES_HELM_WORKLOAD_CONFIG_LABEL = "kubernetes"
""" default config label used to load the workload """
KUBERNETES_HELM_WORKLOAD_CONFIG_BASE = "workload.helm"
""" default config key for creating a workload object """

KUBERNETES_HELM_WORKLOAD_CONFIG_KEY_VERSION = "version"
""" config key for helm version """
KUBERNETES_HELM_WORKLOAD_CONFIG_KEY_REPOS = "repos"
""" config key for helm repos dict which need to be added """
KUBERNETES_HELM_WORKLOAD_CONFIG_KEY_CHART = "chart"
""" config key for helm chart, either local path or http(s) """
KUBERNETES_HELM_WORKLOAD_CONFIG_KEY_VALUESSET = "set"
""" config key for helm chart values """
KUBERNETES_HELM_WORKLOAD_CONFIG_KEY_VALUESFILE_VALUES = "values"
""" config key for helm chart values that should be put into a values file """
KUBERNETES_HELM_WORKLOAD_CONFIG_KEY_VALUESFILE_PATH = "file"
""" config key for helm chart path to values file that we should create """
KUBERNETES_HELM_WORKLOAD_CONFIG_DEFAULT_VALUESFILE_PATH = "values.yml"
""" config default value for helm chart path to values file that we should create """
KUBERNETES_HELM_WORKLOAD_CONFIG_KEY_NAMESPACE = "namespace"
""" config key for namespace to install to """

KUBERNETES_HELM_WORKLOAD_DEFAULT_NAMESPACE = "default"
""" default namespace to install to if no namespace was passed """

KUBERNETES_HELM_WORKLOAD_DEFAULT_BIN = "helm"
""" default helm executble path """
KUBERNETES_HELM_WORKLOAD_DEFAULT_WORKINGDIR = "."
""" default helm working dir for subprocess """


class Status(Enum):
    """A Helm Status enum."""

    UNKNOWN = "unknown"
    DEPLOYED = "deployed"
    UNINSTALLED = "uninstalled"
    SUPERSEDED = "superseded"
    FAILED = "failed"
    UNINSTALLING = "uninstalling"
    PENDING_INSTALL = "pending-install"
    PENDING_UPGRADE = "pending-upgrade"
    PENDING_ROLLBACK = "pending-rollback"


# This is effectively a struct for interpreting the release status information
# pylint: disable=too-few-public-methods, too-many-instance-attributes
class HelmReleaseStatus:
    """Interpreted helm release status.

    Used to formalize the response object from a status request

    """

    def __init__(self, status_response: dict):
        """Interpret status from a status response."""
        self.name = status_response["name"]
        self.version = status_response["version"]
        self.namespace = status_response["namespace"]

        # self.first_deployed = datetime.strptime(status_response['info']['first_deployed'],
        #                                         '%Y-%m-%dT%H:%M:%S.%fZ')
        # self.last_deployed = datetime.strptime(status_response['info']['last_deployed'],
        #                                         '%Y-%m-%dT%H:%M:%S.%fZ')

        self.deleted = status_response["info"]["deleted"]
        self.description = status_response["info"]["description"]
        self.status = Status(status_response["info"]["status"])
        self.notes = status_response["info"]["notes"] if "notes" in status_response["info"] else ""

        self.config = status_response["config"]

        self.manifest = status_response["manifest"]


# pylint: disable=too-many-instance-attributes
class KubernetesHelmWorkloadPlugin:
    """Kubernetes workload class."""

    # this is what we need for this purpose
    # pylint: disable=too-many-arguments
    def __init__(
        self,
        environment,
        instance_id,
        label: str = KUBERNETES_HELM_WORKLOAD_CONFIG_LABEL,
        base: Any = KUBERNETES_HELM_WORKLOAD_CONFIG_BASE,
        helm_bin: str = KUBERNETES_HELM_WORKLOAD_DEFAULT_BIN,
        work_dir: str = KUBERNETES_HELM_WORKLOAD_DEFAULT_WORKINGDIR,
    ):
        """Run the super constructor but also set class properties.

        This implements the args part of the client interface.

        Here we expect to receiv config pointers so that we can determine what
        helm workload to apply, and what values will be needed.

        Parameters:
        -----------
        file (str) : path to where we should put values yaml file

        bin (str) : helm executable path
        dir (dir) : working dir to be used with subprocess

        """
        self._environment: Environment = environment
        """ Environemnt in which this plugin exists """
        self._instance_id: str = instance_id
        """ Unique id for this plugin instance """

        self._config_label: str = label
        """ configerus load label that should contain all of the config """
        self._config_base: str = base
        """ configerus get key that should contain all tf config """

        self._kubeconfig: str = ""
        """Path to a kubeconfig file to be used by helm (see .prepare())."""

        workload_config = self._environment.config().load(self._config_label)

        self.namespace: str = workload_config.get(
            [self._config_base, KUBERNETES_HELM_WORKLOAD_CONFIG_KEY_NAMESPACE],
            default=KUBERNETES_HELM_WORKLOAD_DEFAULT_NAMESPACE,
        )
        """String k8s namespace to constrain created resources."""

        self._chart: str = workload_config.get(
            [self._config_base, KUBERNETES_HELM_WORKLOAD_CONFIG_KEY_CHART]
        )
        """Helm chart to use for the release."""

        self.set: Dict[str, str] = workload_config.get(
            [self._config_base, KUBERNETES_HELM_WORKLOAD_CONFIG_KEY_VALUESSET],
            default={},
        )
        """Dict of --set values."""
        self.values: Dict[str, Any] = workload_config.get(
            [self._config_base, KUBERNETES_HELM_WORKLOAD_CONFIG_KEY_VALUESFILE_VALUES],
            default={},
        )
        """Nested Dict of values to be written to a values file."""
        self._file: str = workload_config.get(
            [self._config_base, KUBERNETES_HELM_WORKLOAD_CONFIG_KEY_VALUESFILE_PATH],
            default=KUBERNETES_HELM_WORKLOAD_CONFIG_DEFAULT_VALUESFILE_PATH,
        )
        """String path to use for the values file."""

        self._repos: Dict[str, str] = workload_config.get(
            [self._config_base, KUBERNETES_HELM_WORKLOAD_CONFIG_KEY_REPOS], default={}
        )
        """Helm repos to be added."""

        self._working_dir: str = work_dir
        """Path to the helm chart, which is used as a python subprocess chdir."""

        if shutil.which(helm_bin) is None:
            raise ValueError(
                "Helm binary not found. Helm commands cannot be called. "
                f"Expected binary at path {helm_bin}"
            )

        self._bin: str = helm_bin
        """Path to the helm binary."""

        # do an initial prepare in case it is never properly run
        try:
            self.prepare()
        # pylint: disable=broad-except
        except Exception:
            pass

    # deep argument is an info() standard across plugins
    # pylint: disable=unused-argument
    def info(self, deep: bool = False):
        """Return dict data about this plugin for introspection."""
        return {
            "release": {
                "name": self._instance_id,
                "repos": self._repos,
                "chart": self._chart,
                "set": self.set,
                "values": self.values,
            },
            "required_fixtures": {
                "kubernetes": {
                    "interface": METTA_PLUGIN_INTERFACE_ROLE_CLIENT,
                    "plugin_id": METTA_PLUGIN_ID_KUBERNETES_CLIENT,
                },
            },
        }

    def health(self) -> Health:
        """Create a Health check for the helm workload."""
        health: Health = Health(source=self._instance_id)

        status = self.status()

        if status.status in [Status.UNKNOWN]:
            health.unknown(
                f"Helm: {self._instance_id} release status is unknown: {status.status} "
                f": {status.description}"
            )

        if status.status in [Status.SUPERSEDED, Status.UNINSTALLING]:
            health.warning(
                f"Helm: {self._instance_id} release status is at issue: {status.status} "
                f": {status.description}"
            )

        if status.status in [Status.DEPLOYED, Status.UNINSTALLED]:
            health.healthy(
                f"Helm: {self._instance_id} release status is good: {status.status} "
                f": {status.description}"
            )

        if status.status == Status.FAILED:
            health.error(
                f"Helm: {self._instance_id} release status is not good: {status.status} "
                f": {status.description}"
            )

        if status.status in [
            Status.PENDING_INSTALL,
            Status.PENDING_UPGRADE,
            Status.PENDING_ROLLBACK,
        ]:
            health.warning(f"Helm status pending: {status.status}")

        return health

    def prepare(self, fixtures: Fixtures = None):
        """Create a workload instance from a set of fixtures.

        Parameters:
        -----------
        fixtures (Fixtures) : a set of fixtures that this workload will use to
            retrieve a kubernetes client plugin.

        """
        if fixtures is None:
            fixtures = self._environment.fixtures()

        try:
            client = fixtures.get_plugin(
                plugin_id=METTA_PLUGIN_ID_KUBERNETES_CLIENT,
            )
        except KeyError as err:
            raise NotImplementedError(
                "Workload could not find the needed client: "
                f"{METTA_PLUGIN_ID_KUBERNETES_CLIENT}"
            ) from err

        self._kubeconfig = client.config_file

    def apply(self, wait: bool = True, debug: bool = False):
        """Apply the helm chart.

        To make the helm apply method reusable, we always run an upgrade with
        the --install flag, which w orks for both the first install, and any
        upgrades run after install

        You need to run the prepare() method before this one.

        Parameters:
        -----------
        wait (bool) : ask the helm client to wait until resources are created
            before returning.

        debug (bool) : ask the helm client for verbose output

        """
        for repo_name, repo_url in self._repos.items():
            self._run(cmd=["repo", "add", repo_name, repo_url])

        cmd = ["upgrade"]
        cmd += [self._instance_id, self._chart]

        cmd += ["--install", "--create-namespace"]

        if wait:
            cmd += ["--wait"]
        if debug:
            cmd += ["--debug"]

        if len(self.set):
            # turn the set dict into '--set a=A,b=B,c=C'
            cmd += [
                "--set",
                ",".join([f"{name}={value}" for (name, value) in self.values.items()]),
            ]

        if len(self.values):
            # turn the values into a file, and add it to the command
            with open(self._file, "w", encoding="utf8") as val_file:
                yaml.dump(self.values, val_file)

            cmd += ["--values", self._file]

        try:
            self._run(cmd=cmd)
        except Exception as err:
            raise RuntimeError("Helm failed to install the release") from err

    # -all is the used command flag, so the var name makes sense
    # pylint: disable=redefined-builtin
    def list(
        self,
        all: bool = False,
        failed: bool = False,
        deployed: bool = False,
        pending: bool = False,
    ):
        """List all releases.

        This is not instance specific but still useful.

        """
        cmd = ["list", "--output=yaml"]

        if all:
            cmd += ["--all"]
        elif deployed:
            cmd += ["--deployed"]
        elif failed:
            cmd += ["--failed"]
        elif pending:
            cmd += ["--pending"]

        list_str = self._run(cmd=cmd, return_output=True)
        if list_str:
            return yaml.safe_load(list_str)

        return []

    def destroy(self, debug: bool = False):
        """Remove an installed helm release.

        Parameters:
        -----------
        debug (bool) : ask the helm client for verbose output

        """
        cmd = ["uninstall", self._instance_id]

        if debug:
            cmd += ["--debug"]

        self._run(cmd=cmd)

    def test(self):
        """Test an installed helm release.

        This runs the helm client test command.

        """
        self._run(cmd=["test", self._instance_id])

    def status(self) -> HelmReleaseStatus:
        """Get status of the installed helm release."""
        try:
            return HelmReleaseStatus(
                yaml.safe_load(
                    self._run(
                        cmd=["status", self._instance_id, "--output=yaml"],
                        return_output=True,
                    )
                )
            )

        except (subprocess.CalledProcessError, AttributeError) as err:
            return HelmReleaseStatus(
                {
                    "name": "unknown",
                    "version": "unknown",
                    "namespace": "unknown",
                    "info": {
                        "deleted": "unknown",
                        "description": str(err),
                        "status": "unknown",
                    },
                    "notes": "Status not found",
                    "config": {},
                    "manifest": [],
                }
            )

    def _run(self, cmd: List[str], return_output: bool = False):
        """Run a helm v3 command."""
        cmd = [
            self._bin,
            f"--kubeconfig={self._kubeconfig}",
            f"--namespace={self.namespace}",
        ] + cmd

        # this syntax makes it easier to read
        # pylint: disable=no-else-return
        if return_output:
            logger.debug("running launchpad command with output capture: %s", " ".join(cmd))
            return_exec: subprocess.CompletedProcess[bytes] = subprocess.run(
                cmd,
                cwd=self._working_dir,
                shell=False,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            return_exec.check_returncode()
            return return_exec.stdout.decode("utf-8")
        else:
            logger.debug("running launchpad command: %s", " ".join(cmd))
            exec: subprocess.CompletedProcess[str] = subprocess.run(
                cmd, cwd=self._working_dir, check=True, text=True
            )
            exec.check_returncode()
            return exec
