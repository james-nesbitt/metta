"""

Metta kubernetes CLI plugin.

Provides functionality to manually interact with the various kubernetes plugins.

"""
import logging
from typing import Dict, Any

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.fixtures import Fixtures
from mirantis.testing.metta.client import METTA_PLUGIN_TYPE_CLIENT
from mirantis.testing.metta.workload import METTA_PLUGIN_TYPE_WORKLOAD
from mirantis.testing.metta_cli.base import CliBase, cli_output

from .kubeapi_client import METTA_PLUGIN_ID_KUBERNETES_CLIENT

logger = logging.getLogger('metta.cli.kubernetes')

METTA_PLUGIN_ID_KUBERNETES_CLI = 'metta_kubernetes'
""" client plugin_id for the metta kubernetes cli plugin """


# this interface is common for all Metta plugins, but CLI plugins underuse it
# pylint: disable=too-few-public-methods
class KubernetesCliPlugin(CliBase):
    """Fire command/group generator for various kubernetes plugin commands."""

    def fire(self) -> Dict[str, Any]:
        """Return command groups for Kubernetes plugins."""
        if self.environment.fixtures.get(plugin_type=METTA_PLUGIN_TYPE_CLIENT,
                                         plugin_id=METTA_PLUGIN_ID_KUBERNETES_CLIENT,
                                         exception_if_missing=False) is not None:

            return {
                'contrib': {
                    'kubernetes': KubernetesGroup(self.environment)
                }
            }

        return {}


class KubernetesGroup():
    """Base Fire command group for terraform client cli commands."""

    def __init__(self, environment: Environment):
        """Add additional command groups for plugins and inject environment."""
        self._environment = environment

        if self._environment.fixtures.get(
                plugin_type=METTA_PLUGIN_TYPE_WORKLOAD, plugin_id='metta_kubernetes_yaml',
                exception_if_missing=False) is not None:
            self.yaml = KubernetesYamlWorkloadGroup(self._environment)
        if self._environment.fixtures.get(
                plugin_type=METTA_PLUGIN_TYPE_WORKLOAD, plugin_id='metta_kubernetes_helm',
                exception_if_missing=False) is not None:
            self.helm = KubernetesHelmWorkloadGroup(self._environment)

    def _select_client(self, instance_id: str = '') -> Fixtures:
        """Pick a matching client."""
        if instance_id:
            return self._environment.fixtures.get(
                plugin_type=METTA_PLUGIN_TYPE_CLIENT, plugin_id='metta_kubernetes',
                instance_id=instance_id)

        # Get the highest priority workload
        return self._environment.fixtures.get(
            plugin_type=METTA_PLUGIN_TYPE_CLIENT, plugin_id='metta_kubernetes')

    def info(self, workload: str = '', deep: bool = False):
        """Get info about a client plugin."""
        fixture = self._select_client(instance_id=workload)

        collect_info = {
            'fixture': {
                'plugin_type': fixture.plugin_type,
                'plugin_id': fixture.plugin_id,
                'instance_id': fixture.instance_id,
                'priority': fixture.priority,
            }
        }

        if deep:
            if hasattr(fixture.plugin, 'info'):
                collect_info.update(fixture.plugin.info())

        return cli_output(collect_info)

    def nodes(self, workload: str = '', node: int = None):
        """Get info about a client plugin."""
        fixture = self._select_client(instance_id=workload)
        nodes = fixture.plugin.nodes()

        if node is None:
            return cli_output(list(node.to_dict() for node in nodes))
        return cli_output(nodes[node].to_dict())

    def nodes_status(self, workload: str = '', node: int = None):
        """Get info about a client plugin."""
        fixture = self._select_client(instance_id=workload)
        nodes = fixture.plugin.nodes()

        if node is None:
            return cli_output(list(node.status.to_dict() for node in nodes))
        return cli_output(nodes[node].status.to_dict())

    def nodes_sysinfo(self, workload: str = '', node: int = None):
        """Get info about a client plugin."""
        fixture = self._select_client(instance_id=workload)

        nodes = fixture.plugin.nodes()

        if node is None:
            return cli_output(list(node.status.node_info.to_dict() for node in nodes))
        return cli_output(nodes[node].status.node_info.to_dict())

    def readyz(self, workload: str = ''):
        """Get kubernetes readiness info from the plugin."""
        plugin = self._select_client(instance_id=workload).plugin

        try:
            return cli_output(plugin.readyz())

        except Exception as err:
            raise RuntimeError('Kubernetes is not ready') from err

    def livez(self, workload: str = ''):
        """Get kubernetes livez info from the plugin."""
        plugin = self._select_client(instance_id=workload).plugin

        try:
            return cli_output(plugin.livez())

        except Exception as err:
            raise RuntimeError("Kubernetes is not ready") from err

    def connect_service_proxy(self, namespace: str,
                              service: str, workload: str = ''):
        """Create a service proxy."""
        plugin = self._select_client(instance_id=workload).plugin

        try:
            # Thank you kubernetes for the naming pattern
            # pylint: disable=invalid-name
            CoreV1Api = plugin.get_api('CoreV1Api')
            sc = CoreV1Api.connect_post_namespaced_service_proxy(namespace=namespace, name=service)

            return cli_output(sc)

        except Exception as err:
            raise RuntimeError("Exception trying to open the service proxy") from err


class KubernetesYamlWorkloadGroup():
    """Base Fire command group for terraform yaml workload plugin cli commands."""

    def __init__(self, environment: Environment):
        """Inject environment into command group object."""
        self._environment = environment

    def _select_fixture(self, instance_id: str = '') -> Fixtures:
        """Pick a matching workload fixture."""
        if instance_id:
            return self._environment.fixtures.get(
                plugin_type=METTA_PLUGIN_TYPE_WORKLOAD, plugin_id='metta_kubernetes_yaml',
                instance_id=instance_id)

        # Get the highest priority workload
        return self._environment.fixtures.get(
            plugin_type=METTA_PLUGIN_TYPE_WORKLOAD, plugin_id='metta_kubernetes_yaml')

    def info(self, workload: str = '', deep: bool = False):
        """Get info about a yaml workload plugin."""
        fixture = self._select_fixture(instance_id=workload)

        collect_info = {
            'fixture': {
                'plugin_type': fixture.plugin_type,
                'plugin_id': fixture.plugin_id,
                'instance_id': fixture.instance_id,
                'priority': fixture.priority,
            }
        }

        if deep:
            if hasattr(fixture.plugin, 'info'):
                collect_info.update(fixture.plugin.info())

        return cli_output(collect_info)

    def apply(self, workload: str = ''):
        """Run workload apply."""
        workload_plugin = self._select_fixture(instance_id=workload).plugin
        instance = workload_plugin.create_instance(self._environment.fixtures)

        objects = instance.apply()

        return cli_output(objects)

    def destroy(self, workload: str = ''):
        """Run workload destroy."""
        workload_plugin = self._select_fixture(instance_id=workload).plugin
        instance = workload_plugin.create_instance(self._environment.fixtures)

        destroy = instance.destroy()

        return cli_output(destroy)


class KubernetesHelmWorkloadGroup():
    """Base Fire command group for terraform helm workload cli commands."""

    def __init__(self, environment: Environment):
        """Inject environment into command group."""
        self._environment = environment

    def _select_fixture(self, instance_id: str = ''):
        """Pick a matching workload fixture."""
        if instance_id:
            return self._environment.fixtures.get(
                plugin_type=METTA_PLUGIN_TYPE_WORKLOAD, plugin_id='metta_kubernetes_helm',
                instance_id=instance_id)

        # Get the highest priority workload
        return self._environment.fixtures.get(
            plugin_type=METTA_PLUGIN_TYPE_WORKLOAD, plugin_id='metta_kubernetes_helm')

    def info(self, workload: str = '', deep: bool = False) -> str:
        """Get info about a helm workload plugin."""
        fixture = self._select_fixture(instance_id=workload)

        collect_info = {
            'fixture': {
                'plugin_type': fixture.plugin_type,
                'plugin_id': fixture.plugin_id,
                'instance_id': fixture.instance_id,
                'priority': fixture.priority,
            }
        }

        if deep:
            if hasattr(fixture.plugin, 'info'):
                collect_info.update(fixture.plugin.info())

        return cli_output(collect_info)

    def apply(self, workload: str = '', wait: bool = True,
              debug: bool = False) -> str:
        """Run helm workload apply."""
        workload_plugin = self._select_fixture(instance_id=workload).plugin
        instance = workload_plugin.create_instance(self._environment.fixtures)

        objects = instance.apply(wait=wait, debug=debug)

        return cli_output(objects)

    def destroy(self, workload: str = '', debug: bool = False) -> str:
        """Run helm workload destroy."""
        workload_plugin = self._select_fixture(instance_id=workload).plugin
        instance = workload_plugin.create_instance(self._environment.fixtures)

        destroy = instance.destroy(debug=debug)

        return cli_output(destroy)
