import logging
from typing import Dict, Any

import json
import yaml

from mirantis.testing.metta.plugin import Type
from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.cli import CliBase

logger = logging.getLogger('metta.cli.kubernetes')


class KubernetesCliPlugin(CliBase):

    def fire(self):
        """ return a dict of commands for aucnhpad provisioenrs if one hase been registered."""
        if self.environment.fixtures.get_fixture(
                type=Type.CLIENT, plugin_id='metta_kubernetes', exception_if_missing=False) is not None:

            return {
                'contrib': {
                    'kubernetes': KubernetesGroup(self.environment)
                }
            }

        else:
            return {}


class KubernetesGroup():

    def __init__(self, environment: Environment):
        self._environment = environment

        if self._environment.fixtures.get_fixture(
                type=Type.WORKLOAD, plugin_id='metta_kubernetes_yaml', exception_if_missing=False) is not None:
            self.yaml = KubernetesYamlWorkloadGroup(self._environment)
        if self._environment.fixtures.get_fixture(
                type=Type.WORKLOAD, plugin_id='metta_kubernetes_helm', exception_if_missing=False) is not None:
            self.helm = KubernetesHelmWorkloadGroup(self._environment)

    def _select_client(self, instance_id: str = ''):
        """ Pick a matching client """
        if instance_id:
            return self._environment.fixtures.get_fixture(
                type=Type.CLIENT, plugin_id='metta_kubernetes', instance_id=instance_id)
        else:
            # Get the highest priority workload
            return self._environment.fixtures.get_fixture(
                type=Type.CLIENT, plugin_id='metta_kubernetes')

    def info(self, workload: str = '', deep: bool = False):
        """ get info about a client plugin """
        fixture = self._select_client(instance_id=workload)

        collect_info = {
            'fixture': {
                'type': fixture.type.value,
                'plugin_id': fixture.plugin_id,
                'instance_id': fixture.instance_id,
                'priority': fixture.priority,
            }
        }

        if deep:
            if hasattr(fixture.plugin, 'info'):
                collect_info.update(fixture.plugin.info(True))

        return json.dumps(collect_info, indent=2)

    def readyz(self, workload: str = '', verbose: bool = False):
        """ get kubernetes readiness info from the plugin """
        plugin = self._select_client(instance_id=workload).plugin

        try:
            return json.dumps(plugin.readyz(verbose=verbose),
                              indent=2, default=lambda x: "{}".format(x))

        except Exception as e:
            raise RuntimeError('Kubernetes is not ready') from e

    def livez(self, workload: str = '', verbose: bool = False):
        """ get kubernetes livez info from the plugin """
        plugin = self._select_client(instance_id=workload).plugin

        try:
            return json.dumps(plugin.livez(verbose=verbose),
                              indent=2, default=lambda x: "{}".format(x))

        except Exception as e:
            raise RuntimeError('Kubernetes is not ready') from e

    def connect_service_proxy(self, namespace: str,
                              service: str, workload: str = ''):
        """ create a service proxy """
        plugin = self._select_client(instance_id=workload).plugin

        try:
            CoreV1Api = plugin.get_api('CoreV1Api')
            sc = CoreV1Api.connect_post_namespaced_service_proxy(
                namespace=namespace, name=service)

            return json.dumps(sc, indent=2, default=lambda x: "{}".format(x))

        except Exception as e:
            raise RuntimeError(
                'Exception trying to open the service proxy') from e


class KubernetesYamlWorkloadGroup():

    def __init__(self, environment: Environment):
        self._environment = environment

    def _select_fixture(self, instance_id: str = ''):
        """ Pick a matching workload fixture """
        if instance_id:
            return self._environment.fixtures.get_fixture(
                type=Type.WORKLOAD, plugin_id='metta_kubernetes_yaml', instance_id=instance_id)
        else:
            # Get the highest priority workload
            return self._environment.fixtures.get_fixture(
                type=Type.WORKLOAD, plugin_id='metta_kubernetes_yaml')

    def info(self, workload: str = '', deep: bool = False):
        """ get info about a yaml workload plugin """
        fixture = self._select_fixture(instance_id=workload)

        collect_info = {
            'fixture': {
                'type': fixture.type.value,
                'plugin_id': fixture.plugin_id,
                'instance_id': fixture.instance_id,
                'priority': fixture.priority,
            }
        }

        if deep:
            if hasattr(fixture.plugin, 'info'):
                collect_info.update(fixture.plugin.info(True))

        return json.dumps(collect_info, indent=2)

    def apply(self, workload: str = ''):
        """ Run workload apply """
        workload = self._select_fixture(instance_id=workload).plugin
        instance = workload.create_instance(self._environment.fixtures)

        objects = instance.apply()

        return json.dumps(objects, indent=2, default=lambda x: "{}".format(x))

    def destroy(self, workload: str = ''):
        """ Run workload destroy """
        workload = self._select_fixture(instance_id=workload).plugin
        instance = workload.create_instance(self._environment.fixtures)

        destroy = instance.destroy()

        return json.dumps(destroy, indent=2)


class KubernetesHelmWorkloadGroup():

    def __init__(self, environment: Environment):
        self._environment = environment

    def _select_fixture(self, instance_id: str = ''):
        """ Pick a matching workload fixture """
        if instance_id:
            return self._environment.fixtures.get_fixture(
                type=Type.WORKLOAD, plugin_id='metta_kubernetes_helm', instance_id=instance_id)
        else:
            # Get the highest priority workload
            return self._environment.fixtures.get_fixture(
                type=Type.WORKLOAD, plugin_id='metta_kubernetes_helm')

    def info(self, workload: str = '', deep: bool = False):
        """ get info about a helm workload plugin """
        fixture = self._select_fixture(instance_id=workload)

        collect_info = {
            'fixture': {
                'type': fixture.type.value,
                'plugin_id': fixture.plugin_id,
                'instance_id': fixture.instance_id,
                'priority': fixture.priority,
            }
        }

        if deep:
            if hasattr(fixture.plugin, 'info'):
                collect_info.update(fixture.plugin.info(True))

        return json.dumps(collect_info, indent=2)

    def apply(self, workload: str = '', wait: bool = True,
              debug: bool = False):
        """ Run helm workload apply """
        workload = self._select_fixture(instance_id=workload).plugin
        instance = workload.create_instance(self._environment.fixtures)

        objects = instance.apply(wait=wait, debug=debug)

        return json.dumps(objects, indent=2, default=lambda x: "{}".format(x))

    def destroy(self, workload: str = '', debug: bool = False):
        """ Run helm workload destroy """
        workload = self._select_fixture(instance_id=workload).plugin
        instance = workload.create_instance(self._environment.fixtures)

        destroy = instance.destroy(debug=debug)

        return json.dumps(destroy, indent=2)
