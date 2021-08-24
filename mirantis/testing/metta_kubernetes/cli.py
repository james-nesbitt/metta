"""

Metta kubernetes CLI plugin.

Provides functionality to manually interact with the various kubernetes plugins.

"""
import logging
from typing import Dict, Any
from subprocess import CalledProcessError

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.fixture import Fixtures
from mirantis.testing.metta_cli.base import CliBase, cli_output

from .kubeapi_client import METTA_PLUGIN_ID_KUBERNETES_CLIENT
from .helm_workload import METTA_PLUGIN_ID_KUBERNETES_HELM_WORKLOAD
from .yaml_workload import METTA_PLUGIN_ID_KUBERNETES_YAML_WORKLOAD
from .deployment_workload import METTA_PLUGIN_ID_KUBERNETES_DEPLOYMENT_WORKLOAD

logger = logging.getLogger("metta.cli.kubernetes")

METTA_PLUGIN_ID_KUBERNETES_CLI = "metta_kubernetes_cli"
""" client plugin_id for the metta kubernetes cli plugin """


# this interface is common for all Metta plugins, but CLI plugins underuse it
# pylint: disable=too-few-public-methods
class KubernetesCliPlugin(CliBase):
    """Fire command/group generator for various kubernetes plugin commands."""

    def fire(self) -> Dict[str, Any]:
        """Return command groups for Kubernetes plugins."""
        if (
            self._environment.fixtures().get(
                plugin_id=METTA_PLUGIN_ID_KUBERNETES_CLIENT,
                exception_if_missing=False,
            )
            is not None
        ):
            return {"kubernetes": KubernetesClientGroup(self._environment)}

        return {}


class KubernetesClientGroup:
    """Kubernetes client CLI commands."""

    def __init__(self, environment: Environment):
        """Add additional command groups for plugins and inject environment."""
        self._environment: Environment = environment

        if (
            self._environment.fixtures().get(
                plugin_id=METTA_PLUGIN_ID_KUBERNETES_YAML_WORKLOAD,
                exception_if_missing=False,
            )
            is not None
        ):
            self.yaml = KubernetesYamlWorkloadGroup(self._environment)
        if (
            self._environment.fixtures().get(
                plugin_id=METTA_PLUGIN_ID_KUBERNETES_HELM_WORKLOAD,
                exception_if_missing=False,
            )
            is not None
        ):
            self.helm = KubernetesHelmWorkloadGroup(self._environment)
        if (
            self._environment.fixtures().get(
                plugin_id=METTA_PLUGIN_ID_KUBERNETES_DEPLOYMENT_WORKLOAD,
                exception_if_missing=False,
            )
            is not None
        ):
            self.deployment = KubernetesDeploymentWorkloadGroup(self._environment)

    def _select_client(self, instance_id: str = "") -> Fixtures:
        """Pick a matching client."""
        if instance_id:
            return self._environment.fixtures().get(
                plugin_id=METTA_PLUGIN_ID_KUBERNETES_CLIENT,
                instance_id=instance_id,
            )

        # Get the highest priority workload
        return self._environment.fixtures().get(plugin_id=METTA_PLUGIN_ID_KUBERNETES_CLIENT)

    def info(self, workload: str = "", deep: bool = False):
        """Get info about a client plugin."""
        fixture = self._select_client(instance_id=workload)
        return cli_output(fixture.info(deep=deep))

    def health(self, client: str = ""):
        """Retrieve the health status from the instance."""
        client_plugin = self._select_client(instance_id=client).plugin
        health = client_plugin.health()
        return cli_output(
            {
                "status": health.status(),
                "messages": list(health.messages()),
            }
        )

    def nodes(self, client: str = "", node: int = None):
        """Get info about a client plugin."""
        client_plugin = self._select_client(instance_id=client).plugin
        nodes = client_plugin.nodes()
        if node is None:
            return cli_output(list(node.to_dict() for node in nodes))
        return cli_output(nodes[node].to_dict())

    def nodes_status(self, client: str = "", node: int = None):
        """Get info about a client plugin."""
        client_plugin = self._select_client(instance_id=client).plugin
        nodes = client_plugin.nodes()
        if node is None:
            return cli_output(list(node.status.to_dict() for node in nodes))
        return cli_output(nodes[node].status.to_dict())

    def nodes_sysinfo(self, client: str = "", node: int = None):
        """Get info about a client plugin."""
        client_plugin = self._select_client(instance_id=client).plugin
        nodes = client_plugin.nodes()
        if node is None:
            return cli_output(list(node.status.node_info.to_dict() for node in nodes))
        return cli_output(nodes[node].status.node_info.to_dict())

    def readyz(self, client: str = ""):
        """Get kubernetes readiness info from the plugin."""
        client_plugin = self._select_client(instance_id=client).plugin
        try:
            return cli_output(client_plugin.readyz())

        except Exception as err:
            raise RuntimeError("Kubernetes is not ready") from err

    def livez(self, client: str = ""):
        """Get kubernetes livez info from the plugin."""
        client_plugin = self._select_client(instance_id=client).plugin
        try:
            return cli_output(client_plugin.livez())

        except Exception as err:
            raise RuntimeError("Kubernetes is not ready") from err

    def connect_service_proxy(self, namespace: str, service: str, client: str = ""):
        """Create a service proxy."""
        client_plugin = self._select_client(instance_id=client).plugin
        try:
            # Thank you kubernetes for the naming pattern
            # pylint: disable=invalid-name
            CoreV1Api = client_plugin.get_api("CoreV1Api")
            sc = CoreV1Api.connect_post_namespaced_service_proxy(namespace=namespace, name=service)

            return cli_output(sc)

        except Exception as err:
            raise RuntimeError("Exception trying to open the service proxy") from err


class KubernetesYamlWorkloadGroup:
    """Base Fire command group for terraform yaml workload plugin cli commands."""

    def __init__(self, environment: Environment):
        """Inject environment into command group object."""
        self._environment: Environment = environment

    def _select_fixture(self, instance_id: str = "") -> Fixtures:
        """Pick a matching workload fixture."""
        if instance_id:
            return self._environment.fixtures().get(
                plugin_id=METTA_PLUGIN_ID_KUBERNETES_YAML_WORKLOAD,
                instance_id=instance_id,
            )

        # Get the highest priority workload
        return self._environment.fixtures().get(plugin_id=METTA_PLUGIN_ID_KUBERNETES_YAML_WORKLOAD)

    def info(self, workload: str = "", deep: bool = False):
        """Get info about a yaml workload plugin."""
        fixture = self._select_fixture(instance_id=workload)
        fixture.plugin.prepare()

        return cli_output(fixture.info(deep=deep))

    def apply(self, workload: str = ""):
        """Run workload apply."""
        workload_plugin = self._select_fixture(instance_id=workload).plugin
        workload_plugin.prepare()

        objects = workload_plugin.apply()

        return cli_output(objects)

    def destroy(self, workload: str = ""):
        """Run workload destroy."""
        workload_plugin = self._select_fixture(instance_id=workload).plugin
        workload_plugin.prepare()

        destroy = workload_plugin.destroy()

        return cli_output(destroy)


class KubernetesHelmWorkloadGroup:
    """Base Fire command group for terraform helm workload cli commands."""

    def __init__(self, environment: Environment):
        """Inject environment into command group."""
        self._environment: Environment = environment

    def _select_fixture(self, instance_id: str = ""):
        """Pick a matching workload fixture."""
        if instance_id:
            return self._environment.fixtures().get(
                plugin_id=METTA_PLUGIN_ID_KUBERNETES_HELM_WORKLOAD,
                instance_id=instance_id,
            )

        # Get the highest priority workload
        return self._environment.fixtures().get(plugin_id=METTA_PLUGIN_ID_KUBERNETES_HELM_WORKLOAD)

    def info(self, workload: str = "", deep: bool = False) -> str:
        """Get info about a helm workload plugin."""
        fixture = self._select_fixture(instance_id=workload)
        fixture.plugin.prepare()

        return cli_output(fixture.info(deep=deep))

    def health(self, workload: str = "") -> str:
        """Get health status info about a helm workload plugin."""
        workload_plugin = self._select_fixture(instance_id=workload).plugin
        workload_plugin.prepare()

        return cli_output(workload_plugin.health())

    def apply(self, workload: str = "", wait: bool = True, debug: bool = False) -> str:
        """Run helm workload apply."""
        workload_plugin = self._select_fixture(instance_id=workload).plugin
        workload_plugin.prepare()

        objects = workload_plugin.apply(wait=wait, debug=debug)

        return cli_output(objects)

    def destroy(self, workload: str = "", debug: bool = False) -> str:
        """Run helm workload destroy."""
        workload_plugin = self._select_fixture(instance_id=workload).plugin
        workload_plugin.prepare()

        destroy = workload_plugin.destroy(debug=debug)

        return cli_output(destroy)

    def status(self, workload: str = "") -> str:
        """Run helm workload destroy."""
        workload_plugin = self._select_fixture(instance_id=workload).plugin
        workload_plugin.prepare()

        try:
            status = workload_plugin.status()
            status_info = {
                "name": status.name,
                "version": status.version,
                "namespace": status.namespace,
                "deleted": status.deleted,
                "description": status.description,
                "status": status.status,
                "config": status.config,
                "manifest": status.manifest,
            }
            return cli_output(status_info)
        except CalledProcessError:
            return cli_output("No status retrievable.")


class KubernetesDeploymentWorkloadGroup:
    """Base Fire command group for terraform deployment workload plugin cli commands."""

    def __init__(self, environment: Environment):
        """Inject environment into command group object."""
        self._environment: Environment = environment

    def _select_fixture(self, instance_id: str = "") -> Fixtures:
        """Pick a matching workload fixture."""
        if instance_id:
            return self._environment.fixtures().get(
                plugin_id=METTA_PLUGIN_ID_KUBERNETES_DEPLOYMENT_WORKLOAD,
                instance_id=instance_id,
            )

        # Get the highest priority workload
        return self._environment.fixtures().get(
            plugin_id=METTA_PLUGIN_ID_KUBERNETES_DEPLOYMENT_WORKLOAD
        )

    def info(self, workload: str = "", deep: bool = False):
        """Get info about workload plugin."""
        fixture = self._select_fixture(instance_id=workload)
        fixture.plugin.prepare()

        return cli_output(fixture.info(deep=deep))

    def health(self, workload: str = ""):
        """Retrieve the results from the deployment workload instance."""
        workload_plugin = self._select_fixture(instance_id=workload).plugin
        workload_plugin.prepare()
        health = workload_plugin.health()

        return cli_output(
            {
                "status": health.status(),
                "messages": list(health.messages()),
            }
        )

    def apply(self, workload: str = ""):
        """Run workload apply."""
        workload_plugin = self._select_fixture(instance_id=workload).plugin
        workload_plugin.prepare()

        objects = workload_plugin.apply()

        return cli_output(objects)

    def destroy(self, workload: str = ""):
        """Run workload destroy."""
        workload_plugin = self._select_fixture(instance_id=workload).plugin
        workload_plugin.prepare()

        destroy = workload_plugin.destroy()

        if destroy is None:
            return "workload not found."
        return cli_output(destroy)
