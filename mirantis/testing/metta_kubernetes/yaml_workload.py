"""

Kubernetes workload plugin for creating infra from a multi-doc yaml file.

This is possible, but not very clean for management of resources.  The python
kubernetes api offers a helper for creating resources, but not easy approach
for removing the resources.

"""

import logging
from typing import List, Any, Dict

import yaml

from mirantis.testing.metta.fixtures import Fixtures
from mirantis.testing.metta.client import METTA_PLUGIN_TYPE_CLIENT
from mirantis.testing.metta.workload import WorkloadBase, WorkloadInstanceBase

from .kubeapi_client import KubernetesApiClientPlugin, METTA_PLUGIN_ID_KUBERNETES_CLIENT

logger = logging.getLogger('metta.contrib.kubernetes.workload.yaml')

KUBERNETES_YAML_WORKLOAD_CONFIG_LABEL = 'kubernetes'
KUBERNETES_YAML_WORKLOAD_CONFIG_BASE = 'workload.yaml'

KUBERNETES_YAML_WORKLOAD_CONFIG_KEY_NAMESPACE = "namespace"
KUBERNETES_YAML_WORKLOAD_CONFIG_DEFAULT_NAMESPACE = "default"
KUBERNETES_YAML_WORKLOAD_CONFIG_KEY_FILE = "file"
KUBERNETES_YAML_WORKLOAD_CONFIG_KEY_YAML = "yaml"

METTA_PLUGIN_ID_KUBERNETES_YAML_WORKLOAD = 'metta_kubernetes_yaml'
""" workload plugin_id for the metta_kubernetes yaml plugin """


class KubernetesYamlWorkloadPlugin(WorkloadBase):
    """Metta workload plugin for Kubernetes workloads created from yaml."""

    def __init__(self, environment, instance_id,
                 label: str = KUBERNETES_YAML_WORKLOAD_CONFIG_LABEL,
                 base: Any = KUBERNETES_YAML_WORKLOAD_CONFIG_BASE):
        """Run the super constructor but also set class properties.

        This implements the args part of the client interface.

        Here we expect to receive a path to a KUBECONFIG file with a context
        set and we create a Kubernetes client for use.  After that this can
        provide Core api clients as per the kubernetes SDK

        Parameters:
        -----------
        config_file (str): String path to the kubernetes config file to use

        """
        self.environment = environment
        """ Environemnt in which this plugin exists """
        self.instance_id = instance_id
        """ Unique id for this plugin instance """

        self.config_label = label
        """ configerus load label that should contain all of the config """
        self.config_base = base
        """ configerus get key that should contain all tf config """

    def create_instance(self, fixtures: Fixtures):
        """Create a workload instance from a set of fixtures.

        Parameters:
        -----------
        fixtures (Fixtures) : a set of fixtures that this workload will use to
            retrieve a kubernetes client plugin.

        """
        try:
            client = fixtures.get_plugin(
                plugin_type=METTA_PLUGIN_TYPE_CLIENT,
                plugin_id=METTA_PLUGIN_ID_KUBERNETES_CLIENT)
        except KeyError as err:
            raise NotImplementedError(
                "Workload could not find the needed client: "
                f"{METTA_PLUGIN_ID_KUBERNETES_CLIENT}") from err

        workload_config = self.environment.config.load(self.config_label)

        namespace = workload_config.get(
            [self.config_base, KUBERNETES_YAML_WORKLOAD_CONFIG_KEY_NAMESPACE],
            default=KUBERNETES_YAML_WORKLOAD_CONFIG_DEFAULT_NAMESPACE)

        # YAML config needs to come from a yaml file path or inline yaml config
        resource_yaml = workload_config.get(
            [self.config_base, KUBERNETES_YAML_WORKLOAD_CONFIG_KEY_YAML], default=[])
        file = workload_config.get(
            [self.config_base, KUBERNETES_YAML_WORKLOAD_CONFIG_KEY_FILE], default='')

        if yaml is None and file == '':
            raise ValueError(
                "Either inline yaml or a file path to a yaml is required.")

        return KubernetesYamlWorkloadInstance(
            client, namespace, data=resource_yaml, file=file)

    def info(self):
        """Return dict data about this plugin for introspection."""
        workload_config = self.environment.config.load(self.config_label)

        return {
            'workload': {
                'deployment': {
                    'namespace': workload_config.get(
                        [self.config_base, KUBERNETES_YAML_WORKLOAD_CONFIG_KEY_NAMESPACE],
                        default=KUBERNETES_YAML_WORKLOAD_CONFIG_DEFAULT_NAMESPACE),
                    'yaml': workload_config.get(
                        [self.config_base, KUBERNETES_YAML_WORKLOAD_CONFIG_KEY_YAML],
                        default='None'),
                    'file': workload_config.get(
                        [self.config_base, KUBERNETES_YAML_WORKLOAD_CONFIG_KEY_FILE],
                        default='None')
                },
                'required_fixtures': {
                    'kubernetes': {
                        'plugin_type': METTA_PLUGIN_TYPE_CLIENT,
                        'plugin_id': 'metta_kubernetes'
                    }
                }
            }
        }


# @TODO create a remove method as well.
# pylint: disable=too-few-public-methods
class KubernetesYamlWorkloadInstance(WorkloadInstanceBase):
    """Instance of the k8s yaml workload, used to manage a particular run.

    Parameters:
    -----------
    client (kubeapi_client) : metta kubernetes kubeapi_client object

    namespace (str) : string namespace to use for all craeted resources

    data (Dict[str, Any]) : laoded yaml content to be passed to the kubeapi client

    OR

    file (str) : file path to a file containing the yaml.

    """

    def __init__(self, client: KubernetesApiClientPlugin, namespace: str,
                 data: Dict[str, Any], file: str):
        """Comfigure new workload instance."""
        self.client = client
        self.namespace = namespace
        self.data = data
        self.file = file

        self.k8s_objects: List[object] = []

    def apply(self):
        """Use the passed yaml to create k8s resources.

        Returns:
        --------
        Any created resources.

        """
        if self.file:
            with open(self.file) as res_file:
                resources_yaml = yaml.safe_load_all(res_file)

                for resource in resources_yaml:
                    self.k8s_objects.append(self.client.utils_create_from_dict(
                        data=resource,
                        namespace=self.namespace
                    ))

        else:
            with open('./temp.yaml','w') as temp_file:
                temp_file.write(yaml.safe_dump(self.data))
            self.k8s_objects.append(self.client.utils_create_from_dict(
                data=self.data,
                namespace=self.namespace
            ))

        return self.k8s_objects

    # @TODO write the docker container rm
    def destroy(self):
        """Destroy a created docker run."""
