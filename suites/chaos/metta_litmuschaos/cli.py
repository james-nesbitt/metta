import logging
from typing import Dict, Any
import time
import json
import yaml

from mirantis.testing.metta.plugin import Type
from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.cli import CliBase

from .litmuschaos_workload import METTA_PLUGIN_ID_LITMUSCHAOS_WORKLOAD

logger = logging.getLogger('metta.cli.litmuschaos')

METTA_PLUGIN_ID_LITMUSCHAOS_cli = 'metta_litmuschaos_cli'
""" cli plugin_id for the litmuschaos plugin """


class LitmusChaosCliPlugin(CliBase):

    def fire(self):
        """ return a dict of commands for litmuschaos workloads if one hase been registered."""
        if self.environment.fixtures.get_fixture(
                type=Type.WORKLOAD, plugin_id=METTA_PLUGIN_ID_LITMUSCHAOS_WORKLOAD, exception_if_missing=False) is not None:
            return {
                'contrib': {
                    'litmuschaos': LitmusChaosGroup(self.environment)
                }
            }
        else:
            return {}


class LitmusChaosGroup():
    """ LitmusChaos workload plugin cli command group """

    def __init__(self, environment: Environment):
        self.environment = environment

    def _select_fixture(self, instance_id: str = ''):
        """ Pick a matching workload plugin """
        try:
            if instance_id:
                return self.environment.fixtures.get_fixture(
                    type=Type.WORKLOAD, plugin_id=METTA_PLUGIN_ID_LITMUSCHAOS_WORKLOAD, instance_id=instance_id)
            else:
                # Get the highest priority provisioner
                return self.environment.fixtures.get_fixture(
                    type=Type.WORKLOAD, plugin_id=METTA_PLUGIN_ID_LITMUSCHAOS_WORKLOAD)

        except KeyError as e:
            raise ValueError(
                "No usable kubernetes client was found for litmuschaos to pull a kubeconfig from: {}".format(e)) from e

    def _select_instance(self, instance_id: str = ''):
        """ create a litmuschaos workload plugin instance """
        fixture = self._select_fixture(instance_id=instance_id)
        plugin = fixture.plugin
        # @TODO allow filtering of kubernetes client instances
        instance = plugin.create_instance(self.environment.fixtures)
        return instance

    def info(self, instance_id: str = '', deep: bool = False):
        """ get info about the plugin """
        fixture = self._select_fixture(instance_id=instance_id)

        info = {
            'fixture': {
                'type': fixture.type.value,
                'plugin_id': fixture.plugin_id,
                'instance_id': fixture.instance_id,
                'priority': fixture.priority,
            },
        }

        if deep:
            if hasattr(fixture.plugin, 'info'):
                info.update(fixture.plugin.info(True))

            instance = self._select_instance(instance_id=instance_id)
            info['instance'] = instance.info(deep)

        return json.dumps(info, indent=2)


    def prepare(self):
        """ Prepare the workload instance for running """
        instance = self._select_instance(instance_id=instance_id)

        instance.prepare()
