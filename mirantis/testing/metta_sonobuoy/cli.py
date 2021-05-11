import logging
from typing import Dict, Any
import time
import json
import yaml

from mirantis.testing.metta.plugin import Type
from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.cli import CliBase

from .sonobuoy import METTA_PLUGIN_ID_SONOBUOY_WORKLOAD, Status

logger = logging.getLogger('metta.cli.sonobuoy')

METTA_PLUGIN_ID_SONOBUOY_cli = 'metta_sonobuoy_cli'
""" cli plugin_id for the sonobuoy plugin """


class SonobuoyCliPlugin(CliBase):

    def fire(self):
        """ return a dict of commands for sonobuoy workloads if one hase been registered."""
        if self.environment.fixtures.get_fixture(
                type=Type.WORKLOAD, plugin_id=METTA_PLUGIN_ID_SONOBUOY_WORKLOAD, exception_if_missing=False) is not None:
            return {
                'contrib': {
                    'sonobuoy': SonobuoyGroup(self.environment)
                }
            }
        else:
            return {}


class SonobuoyGroup():
    """ Sonobuoy workload plugin cli command group """

    def __init__(self, environment: Environment):
        self.environment = environment

    def _select_fixture(self, instance_id: str = ''):
        """ Pick a matching workload plugin """
        try:
            if instance_id:
                return self.environment.fixtures.get_fixture(
                    type=Type.WORKLOAD, plugin_id=METTA_PLUGIN_ID_SONOBUOY_WORKLOAD, instance_id=instance_id)
            else:
                # Get the highest priority provisioner
                return self.environment.fixtures.get_fixture(
                    type=Type.WORKLOAD, plugin_id=METTA_PLUGIN_ID_SONOBUOY_WORKLOAD)

        except KeyError as e:
            raise ValueError(
                "No usable kubernetes client was found for sonobuoy to pull a kubeconfig from: {}".format(e)) from e

    def _select_instance(self, instance_id: str = ''):
        """ create a sonobuoy workload plugin instance """
        fixture = self._select_fixture(instance_id=instance_id)
        plugin = fixture.plugin
        # @TODO allow filtering of kubernetes client instances
        instance = plugin.create_instance(self.environment.fixtures)
        return instance

    def info(self, instance_id: str = '', deep: bool = False):
        """ get info about a provisioner plugin """
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
                info.update(fixture.plugin.info(True))

        return json.dumps(info, indent=2)

    def status(self, instance_id: str = ''):
        """ get active sonobuoy status """
        instance = self._select_instance(instance_id=instance_id)
        status = instance.status()

        if status is None:
            status_info = {
                'status': "None",
            }
        else:
            status_info = {
                'status': status.status.value,
                'plugins': {plugin_id: status.plugin(plugin_id) for plugin_id in status.plugin_list()}
            }

        return json.dumps(status_info, indent=2)

    def crb(self, instance_id: str = '', remove: bool = False):
        """ create the crb needed to run sonobuoy """
        instance = self._select_instance(instance_id=instance_id)

        if remove:
            instance._delete_k8s_crb()
        else:
            instance._create_k8s_crb()

    def run(self, instance_id: str = '', wait: bool = False):
        """ run sonobuoy workload """
        instance = self._select_instance(instance_id=instance_id)
        instance.run(wait=wait)

    def wait(self, instance_id: str = '', step: int = 5, limit: int = 1000):
        """ wait until no longer running """
        instance = self._select_instance(instance_id=instance_id)
        print('{')
        for i in range(0, limit):
            status = instance.status()
            if status is None:
                status_info = {
                    'status': "None",
                }
            else:
                status_info = {
                    'status': status.status.value,
                    'plugins': {plugin_id: status.plugin(plugin_id) for plugin_id in status.plugin_list()}
                }

            print("{}: {},".format(i, status_info))
            if status is None or status.status not in [Status.RUNNING]:
                break

            time.sleep(step)
        print('}')

    def destroy(self, instance_id: str = '', wait: bool = False):
        """ remove all sonobuoy infrastructure """
        instance = self._select_instance(instance_id=instance_id)
        instance.destroy(wait=wait)

    def logs(self, instance_id: str = '', follow: bool = False):
        """ sonobuoy logs """
        instance = self._select_instance(instance_id=instance_id)
        instance.logs(follow=follow)

    def retrieve(self, instance_id: str = ''):
        """ retrieve the results from the sonobuoy workload instance """
        instance = self._select_instance(instance_id=instance_id)
        try:
            instance.retrieve()
        except Exception as e:
            logger.error("Retrieve failed: {}".format(e))
