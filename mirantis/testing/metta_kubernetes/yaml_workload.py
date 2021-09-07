"""

Kubernetes workload plugin for creating infra from a multi-doc yaml file.

This is possible, but not very clean for management of resources.  The python
kubernetes api offers a helper for creating resources, but not easy approach
for removing the resources.

"""

import logging
from typing import List, Any, Dict

import yaml

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.fixture import Fixtures
from mirantis.testing.metta.client import METTA_PLUGIN_INTERFACE_ROLE_CLIENT

from .kubeapi_client import KubernetesApiClientPlugin, METTA_PLUGIN_ID_KUBERNETES_CLIENT

logger = logging.getLogger("metta.contrib.kubernetes.workload.yaml")

KUBERNETES_YAML_WORKLOAD_CONFIG_LABEL = "kubernetes"
KUBERNETES_YAML_WORKLOAD_CONFIG_BASE = "workload.yaml"

KUBERNETES_YAML_WORKLOAD_CONFIG_KEY_NAMESPACE = "namespace"
KUBERNETES_YAML_WORKLOAD_CONFIG_DEFAULT_NAMESPACE = "default"
KUBERNETES_YAML_WORKLOAD_CONFIG_KEY_FILE = "file"
KUBERNETES_YAML_WORKLOAD_CONFIG_KEY_YAML = "yaml"

METTA_PLUGIN_ID_KUBERNETES_YAML_WORKLOAD = "metta_kubernetes_yaml_workload"
""" workload plugin_id for the metta_kubernetes yaml plugin """


# pylint: disable=too-many-instance-attributes
class KubernetesYamlWorkloadPlugin:
    """Metta workload plugin for Kubernetes workloads created from yaml."""

    def __init__(
        self,
        environment,
        instance_id,
        label: str = KUBERNETES_YAML_WORKLOAD_CONFIG_LABEL,
        base: Any = KUBERNETES_YAML_WORKLOAD_CONFIG_BASE,
    ):
        """Run the super constructor but also set class properties.

        This implements the args part of the client interface.

        Here we expect to receive a path to a KUBECONFIG file with a context
        set and we create a Kubernetes client for use.  After that this can
        provide Core api clients as per the kubernetes SDK

        Parameters:
        -----------
        config_file (str): String path to the kubernetes config file to use

        """
        self._environment: Environment = environment
        """ Environemnt in which this plugin exists """
        self._instance_id: str = instance_id
        """ Unique id for this plugin instance """

        self._config_label = label
        """ configerus load label that should contain all of the config """
        self._config_base = base
        """ configerus get key that should contain all tf config """

        workload_config = self._environment.config().load(self._config_label)

        self.namespace = workload_config.get(
            [self._config_base, KUBERNETES_YAML_WORKLOAD_CONFIG_KEY_NAMESPACE],
            default=KUBERNETES_YAML_WORKLOAD_CONFIG_DEFAULT_NAMESPACE,
        )

        # YAML config needs to come from a yaml file path or inline yaml config
        self.resource_yaml: Dict[str, Any] = workload_config.get(
            [self._config_base, KUBERNETES_YAML_WORKLOAD_CONFIG_KEY_YAML], default={}
        )
        """Inline YAML/Dict to source k8s resources."""
        self.file = workload_config.get(
            [self._config_base, KUBERNETES_YAML_WORKLOAD_CONFIG_KEY_FILE], default=""
        )
        """YAML file which will source the k8s resources."""

        if self.resource_yaml is None and self.file == "":
            raise ValueError("Either inline yaml or a file path to a yaml is required.")

        self.client: KubernetesApiClientPlugin = None
        """KubeAPI client to connect to the cluster (see prepare())."""

        self.k8s_objects: List[object] = []
        """List of resource creation objects."""

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
        workload_config = self._environment.config().load(self._config_label)

        return {
            "workload": {
                "deployment": {
                    "namespace": workload_config.get(
                        [
                            self._config_base,
                            KUBERNETES_YAML_WORKLOAD_CONFIG_KEY_NAMESPACE,
                        ],
                        default=KUBERNETES_YAML_WORKLOAD_CONFIG_DEFAULT_NAMESPACE,
                    ),
                    "yaml": workload_config.get(
                        [self._config_base, KUBERNETES_YAML_WORKLOAD_CONFIG_KEY_YAML],
                        default="None",
                    ),
                    "file": workload_config.get(
                        [self._config_base, KUBERNETES_YAML_WORKLOAD_CONFIG_KEY_FILE],
                        default="None",
                    ),
                },
                "required_fixtures": {
                    "kubernetes": {
                        "interfaces": [METTA_PLUGIN_INTERFACE_ROLE_CLIENT],
                        "plugin_id": METTA_PLUGIN_ID_KUBERNETES_CLIENT,
                    }
                },
            }
        }

    def prepare(self, fixtures: Fixtures = None):
        """Get the kubeapi client from a set of fixtures.

        Parameters:
        -----------
        fixtures (Fixtures) : a set of fixtures that this workload will use to
            retrieve a kubernetes client plugin.

        """
        if fixtures is None:
            fixtures = self._environment.fixtures()

        try:
            self.client = fixtures.get_plugin(plugin_id=METTA_PLUGIN_ID_KUBERNETES_CLIENT)
        except KeyError as err:
            raise NotImplementedError(
                "Workload could not find the needed client: "
                f"{METTA_PLUGIN_ID_KUBERNETES_CLIENT}"
            ) from err

    def apply(self):
        """Use the passed yaml to create k8s resources.

        Returns:
        --------
        Any created resources.

        """
        if self.file:
            with open(self.file, encoding="utf8") as res_file:
                resources_yaml = yaml.safe_load_all(res_file)

                for resource in resources_yaml:
                    self.k8s_objects.append(
                        self.client.utils_create_from_dict(data=resource, namespace=self.namespace)
                    )

        else:
            self.k8s_objects.append(
                self.client.utils_create_from_dict(
                    data=self.resource_yaml, namespace=self.namespace
                )
            )

        return self.k8s_objects

    # @TODO write the docker container rm
    def destroy(self):
        """Destroy a created docker run."""
