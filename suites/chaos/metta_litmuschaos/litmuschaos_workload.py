"""

Run a LitmusChaos run on a k8s client

"""
from typing import Dict, Any, List
import logging
import subprocess
import os
import json
import yaml
from enum import Enum, unique

from configerus.loaded import LOADED_KEY_ROOT
from configerus.contrib.jsonschema.validate import PLUGIN_ID_VALIDATE_JSONSCHEMA_SCHEMA_CONFIG_LABEL
from configerus.validator import ValidationError

from mirantis.testing.metta.plugin import Type
from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.fixtures import Fixtures
from mirantis.testing.metta.workload import WorkloadBase, WorkloadInstanceBase
from mirantis.testing.metta_kubernetes import METTA_PLUGIN_ID_KUBERNETES_CLIENT

from .litmuschaos import LitmusChaos, LITMUSCHAOS_OPERATOR_DEFAULT_VERSION, LITMUSCHAOS_CONFIG_DEFAULT_EXPERIMENTS

logger = logging.getLogger('workload.litmuschaos')

METTA_PLUGIN_ID_LITMUSCHAOS_WORKLOAD = 'metta_litmuschaos_run'
""" workload plugin_id for the litmuschaos plugin """

LITMUSCHAOS_WORKLOAD_CONFIG_LABEL = 'litmuschaos'
""" Configerus label for retrieving LitmusChaos config """
LITMUSCHAOS_WORKLOAD_CONFIG_BASE = LOADED_KEY_ROOT
""" Configerus get base for retrieving the default workload config """

LITMUSCHAOS_CONFIG_KEY_NAMESPACE = "namespace"
""" Config key to find out what kubernetes namespace to run chaos in. """
LITMUSCHAOS_CONFIG_DEFAULT_NAMESPACE = "default"
""" Default value for kubernetes namespace to run chaos in. """

LITMUSCHAOS_CONFIG_KEY_VERSION = "version"
""" Config key to find out what litmus chaos version to run """

LITMUSCHAOS_CONFIG_KEY_EXPERIMENTS = "experiments"
""" Config key to find out what litmus chaos experiemnts to run. """


LITMUSCHAOS_VALIDATE_JSONSCHEMA = {
    'type': 'object',
    'properties': {
        'type': {'type': 'string'},
        'plugin_id': {'type': 'string'},

        'version': {'type': 'string'},

        'experiments': {
            'type': 'array',
            'items': {'type': 'string'}
        },

    },
    'required': ['experiments']
}
""" Validation jsonschema for litmuschaos config contents """
LITMUSCHAOS_VALIDATE_TARGET = {
    PLUGIN_ID_VALIDATE_JSONSCHEMA_SCHEMA_CONFIG_LABEL: LITMUSCHAOS_VALIDATE_JSONSCHEMA}
""" configerus validation target to match the jsonschema config """


class LitmusChaosWorkloadPlugin(WorkloadBase):
    """ Workload class for the LitmusChaos """

    def __init__(self, environment: Environment, instance_id: str,
                 label: str = LITMUSCHAOS_WORKLOAD_CONFIG_LABEL, base: Any = LITMUSCHAOS_WORKLOAD_CONFIG_BASE):
        """ Run the super constructor but also set class properties

        Parameters:
        -----------

        label (str) : Configerus label for loading config
        base (Any) : configerus base key which should contain all of the config

        """
        WorkloadBase.__init__(self, environment, instance_id)

        logger.info("Preparing litmuschaos settings")

        self.config_label = label
        """ configerus load label that should contain all of the config """
        self.config_base = base
        """ configerus get key that should contain all tf config """

    def info(self, deep: bool = False):
        """ Return plugin info in an object/dict format for debugging """

        config_loaded = self.environment.config.load(self.config_label)

        info = {
            'config': {
                'label': self.config_label,
                'base': self.config_base,
                'contents': config_loaded.get(self.config_base, default={})
            }
        }

        return info

    def create_instance(self, fixtures: Fixtures):
        """ Create a workload instance from a set of fixtures

        Parameters:
        -----------

        fixtures (Fixtures) : a set of fixtures that this workload will use to
            retrieve a kubernetes api client plugin.

        """

        loaded = self.environment.config.load(self.config_label)
        """ get a configerus LoadedConfig for the sonobuoy label """

        # Validate the config overall using jsonschema
        try:
            litmuschaos_config = loaded.get(
                self.config_base,
                validator=LITMUSCHAOS_VALIDATE_TARGET)
        except ValidationError as e:
            raise ValueError(
                "Invalid litmus chaos config received: {}".format(e)) from e

        kube_client = fixtures.get_plugin(
            type=Type.CLIENT, plugin_id=METTA_PLUGIN_ID_KUBERNETES_CLIENT)

        namespace = loaded.get(
            [self.config_base, LITMUSCHAOS_CONFIG_KEY_NAMESPACE], default=LITMUSCHAOS_CONFIG_DEFAULT_NAMESPACE)

        version = loaded.get(
            [self.config_base, LITMUSCHAOS_CONFIG_KEY_VERSION], default=LITMUSCHAOS_OPERATOR_DEFAULT_VERSION)

        experiments = loaded.get(
            [self.config_base, LITMUSCHAOS_CONFIG_KEY_EXPERIMENTS], default=LITMUSCHAOS_CONFIG_DEFAULT_EXPERIMENTS)

        return LitmusChaosWorkloadPluginInstance(
            kube_client=kube_client, namespace=namespace, version=version, experiments=experiments)


class LitmusChaosWorkloadPluginInstance():
    """ Individual instance of the LitmusChaos workload for execution """

    def __init__(self, kube_client: str, namespace: str,
                 version: str, experiments: List[str]):
        """

        Parameters:
        -----------

        kube_client (METTA_PLUGIN_ID_KUBERNETES_CLIENT) : metta_kubernetes
            kube_client client plugin. Used to interact with the kubernetes cluster

        namespace (str) : kubernetes namespace to run chaos in

        version (str) : litmus chaos version to use

        experiments (List[str]) : litmus chaos experiments to run

        """

        self.litmuschaos = LitmusChaos(
            kube_client=kube_client,
            namespace=namespace,
            version=version,
            experiments=experiments)

    def info(self, deep: bool = False):
        """ return an object/dict of inforamtion about the instance for debugging """

        info = {
            'client': self.litmuschaos.info(deep)
        }

        return info

    def prepare(self):
        """ prepare to run litmus chaos by installing all of the pre-requisites """
        self.litmuschaos.prepare()

    def apply(self):
        """ Run the Litmus Chaos experiments """

    def destroy(self):
        """ remove all litmus chaos components from the cluster """
