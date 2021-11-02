"""

Metta client plugin for sonobuoy.

Metta client plugin which provides an injectable metta plugin for interacting
with the SonobuoyClient code with an applied set of configuration.
These are typically provided by the other plugins, but could be created
directly if you can pass the arguments in.

"""
from typing import List, Dict
import subprocess

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta_health.healthcheck import Health

from mirantis.testing.metta_kubernetes.kubeapi_client import KubernetesApiClientPlugin

from .sonobuoy import SonobuoyClient, SONOBUOY_DEFAULT_RESULTS_PATH
from .plugin import Plugin
from .results import (
    Status,
    SonobuoyStatus,
    SonobuoyResults,
)

METTA_SONOBUOY_CLIENT_PLUGIN_ID = "metta_sonobuoy_client"
""" workload plugin_id for the sonobuoy plugin """


class SonobuoyClientPlugin:
    """Metta client plugin for sonobuoy."""

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        environment: Environment,
        instance_id: str,
        kubeclient: KubernetesApiClientPlugin,
        plugins: List[Plugin] = None,
        results_path: str = SONOBUOY_DEFAULT_RESULTS_PATH,
    ):
        """Gather enough arguments to configure the SonobuoyClient object."""
        self._environment: Environment = environment
        """ Environemnt in which this plugin exists """
        self._instance_id: str = instance_id
        """ Unique id for this plugin instance """

        self._sonobuoy: SonobuoyClient = SonobuoyClient(
            kubeclient=kubeclient,
            plugins=plugins,
            results_path=results_path,
        )

    # the deep argument is a standard for the info hook
    # pylint: disable=unused-argument
    def info(self, deep: bool = False):
        """Return dict data about this plugin for introspection."""
        return {
            "client": self._sonobuoy.info(deep=deep) if self._sonobuoy is not None else "MISSING"
        }

    def run(self, wait: bool = True, run_args: List[str] = None):
        """Run sonobuoy."""
        return self._sonobuoy.run(wait=wait, run_args=run_args)

    def status(self) -> SonobuoyStatus:
        """Retrieve Sonobuoy status return."""
        return self._sonobuoy.status()

    def logs(self, follow: bool = True):
        """Output sonobuoy logs."""
        return self._sonobuoy.logs(follow=follow)

    def results(self) -> str:
        """Retrieve sonobuoy results."""
        return self._sonobuoy.results()

    def retrieve(self) -> SonobuoyResults:
        """Retrieve sonobuoy results."""
        return self._sonobuoy.retrieve()

    def delete(self, wait: bool = False):
        """Delete sonobuoy resources."""
        return self._sonobuoy.delete(wait=wait)

    def version(self) -> Dict[str, str]:
        """Retrieve sonobuoy version."""
        return self._sonobuoy.version()

    def health(self) -> Health:
        """Perform a health check on the workload."""
        health = Health(source=self._instance_id)

        try:
            status = self.status()

            if status.status in [Status.POSTPROCESS]:
                health.info("Sonobuoy: run has finished, but result is not yet avaialble.")
            elif status.status in [Status.COMPLETE, Status.PASSED]:
                health.info("Sonobuoy: completed.")
            elif status.status in [Status.FAILED]:
                health.error("Sonobuoy: run has produced a failure.")
            else:  # if status.status() in [Status.PENDING, Status.RUNNING]:
                health.info("Sonobuoy: Running")

        except (subprocess.CalledProcessError, AttributeError) as err:
            health.unknown(f"No status found. Sonobuoy is likely not running: {err}")

        return health

    def create_k8s_crb(self):
        """Create the cluster role binding that sonobuoy needs."""
        return self._sonobuoy.create_k8s_crb()

    def delete_k8s_crb(self):
        """Remove the cluster role binding that we created."""
        return self._sonobuoy.delete_k8s_crb()
