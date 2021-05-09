"""

Kubernetes workload plugin for creating infra from a multi-doc yaml file

"""

import logging
from typing import List, Any, Dict
import yaml

from mirantis.testing.metta.plugin import Type
from mirantis.testing.metta.fixtures import Fixtures
from mirantis.testing.metta.workload import WorkloadBase, WorkloadInstanceBase

logger = logging.getLogger('metta.contrib.kubernetes.workload.yaml')

KUBERNETES_YAML_WORKLOAD_CONFIG_LABEL = 'kubernetes'
KUBERNETES_YAML_WORKLOAD_CONFIG_BASE = 'workload.yaml'

KUBERNETES_YAML_WORKLOAD_CONFIG_KEY_NAMESPACE = "namespace"
KUBERNETES_YAML_WORKLOAD_CONFIG_DEFAULT_NAMESPACE = "default"
KUBERNETES_YAML_WORKLOAD_CONFIG_KEY_FILE = "file"
KUBERNETES_YAML_WORKLOAD_CONFIG_KEY_YAML = "yaml"


class KubernetesYamlWorkloadPlugin(WorkloadBase):
    """ Kubernetes workload class """

    def __init__(self, environment, instance_id,
                 label: str = KUBERNETES_YAML_WORKLOAD_CONFIG_LABEL, base: Any = KUBERNETES_YAML_WORKLOAD_CONFIG_BASE):
        """ Run the super constructor but also set class properties

        This implements the args part of the client interface.

        Here we expect to receive a path to a KUBECONFIG file with a context set
        and we create a Kubernetes client for use.  After that this can provide
        Core api clients as per the kubernetes SDK

        Parameters:
        -----------

        config_file (str): String path to the kubernetes config file to use

        """
        WorkloadBase.__init__(self, environment, instance_id)

        self.config_label = label
        """ configerus load label that should contain all of the config """
        self.config_base = base
        """ configerus get key that should contain all tf config """

    def create_instance(self, fixtures: Fixtures):
        """ Create a workload instance from a set of fixtures

        Parameters:
        -----------

        fixtures (Fixtures) : a set of fixtures that this workload will use to
            retrieve a kubernetes client plugin.

        """

        try:
            client = fixtures.get_plugin(
                type=Type.CLIENT, plugin_id='metta_kubernetes')
        except KeyError as e:
            raise NotImplementedError(
                "Workload could not find the needed client: {}".format('metta_kubernetes'))

        workload_config = self.environment.config.load(self.config_label)

        namespace = workload_config.get(
            [self.config_base, KUBERNETES_YAML_WORKLOAD_CONFIG_KEY_NAMESPACE], default=KUBERNETES_YAML_WORKLOAD_CONFIG_DEFAULT_NAMESPACE)

        """ YAML config needs to come from either a yaml file path or inline yaml config """
        yaml = workload_config.get(
            [self.config_base, KUBERNETES_YAML_WORKLOAD_CONFIG_KEY_YAML], default=[])
        file = workload_config.get(
            [self.config_base, KUBERNETES_YAML_WORKLOAD_CONFIG_KEY_FILE], default=None)

        if yaml is None and file is None:
            raise ValueError(
                "Either inline yaml or a file path to a yaml is required.")

        return KubernetesYamlWorkloadInstance(
            client, namespace, data=yaml, file=file)

    def info(self, deep: bool = False):
        """ Return dict data about this plugin for introspection """
        workload_config = self.environment.config.load(self.config_label)

        return {
            'workload': {
                'deployment': {
                    'namespace': workload_config.get(
                        [self.config_base, KUBERNETES_YAML_WORKLOAD_CONFIG_KEY_NAMESPACE], default=KUBERNETES_YAML_WORKLOAD_CONFIG_DEFAULT_NAMESPACE),
                    'yaml': workload_config.get(
                        [self.config_base, KUBERNETES_YAML_WORKLOAD_CONFIG_KEY_YAML], default='None'),
                    'file': workload_config.get(
                        [self.config_base, KUBERNETES_YAML_WORKLOAD_CONFIG_KEY_FILE], default='None')
                },
                'required_fixtures': {
                    'kubernetes': {
                        'type': Type.CLIENT.value,
                        'plugin_id': 'metta_kubernetes'
                    }
                }
            }
        }


class KubernetesYamlWorkloadInstance(WorkloadInstanceBase):

    def __init__(self, client, namespace: str,
                 data: Dict[str, Any], file: str):
        self.client = client
        self.namespace = namespace
        self.data = data
        self.file = file

        self.k8s_objects = []

    def apply(self):
        """ Run the workload """
        if self.file:
            with open(self.file) as r:
                resources_yaml = yaml.safe_load_all(r)

                for resource in resources_yaml:
                    self.k8s_objects.append(self.client.utils_create_from_dict(
                        data=resource,
                        namespace=self.namespace
                    ))

        else:
            self.k8s_object.append(self.client.utils_create_from_dict(
                data=self.data,
                namespace=self.namespace
            ))
        return self.k8s_objects
