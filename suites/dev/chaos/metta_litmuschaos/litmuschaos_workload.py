"""

Run a LitmusChaos run on a k8s client

"""
from typing import Any, List
import logging

from configerus.loaded import LOADED_KEY_ROOT
from configerus.contrib.jsonschema.validate import (
    PLUGIN_ID_VALIDATE_JSONSCHEMA_SCHEMA_CONFIG_LABEL,
)
from configerus.validator import ValidationError

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.fixture import Fixtures
from mirantis.testing.metta.client import METTA_PLUGIN_INTERFACE_ROLE_CLIENT
from mirantis.testing.metta_kubernetes import METTA_PLUGIN_ID_KUBERNETES_CLIENT

from .litmuschaos import (
    LitmusChaos,
    LITMUSCHAOS_OPERATOR_DEFAULT_VERSION,
    LITMUSCHAOS_CONFIG_DEFAULT_EXPERIMENTS,
)

logger = logging.getLogger("metta_litmuschaos.workload")

METTA_PLUGIN_ID_LITMUSCHAOS_WORKLOAD = "metta_litmuschaos_run"
""" workload plugin_id for the litmuschaos plugin """

LITMUSCHAOS_WORKLOAD_CONFIG_LABEL = "litmuschaos"
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
    "type": "object",
    "properties": {
        "type": {"type": "string"},
        "plugin_id": {"type": "string"},
        "version": {"type": "string"},
        "experiments": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["experiments"],
}
""" Validation jsonschema for litmuschaos config contents """
LITMUSCHAOS_VALIDATE_TARGET = {
    PLUGIN_ID_VALIDATE_JSONSCHEMA_SCHEMA_CONFIG_LABEL: LITMUSCHAOS_VALIDATE_JSONSCHEMA
}
""" configerus validation target to match the jsonschema config """


class LitmusChaosWorkloadPlugin:
    """Workload class for the LitmusChaos."""

    def __init__(
        self,
        environment: Environment,
        instance_id: str,
        label: str = LITMUSCHAOS_WORKLOAD_CONFIG_LABEL,
        base: Any = LITMUSCHAOS_WORKLOAD_CONFIG_BASE,
    ):
        """Configure workload plugin object.

        Parameters:
        -----------
        label (str) : Configerus label for loading config
        base (Any) : configerus base key which should contain all of the config

        """
        self._environment: Environment = environment
        """ Environemnt in which this plugin exists """
        self._instance_id: str = instance_id
        """ Unique id for this plugin instance """

        self.config_label = label
        """ configerus load label that should contain all of the config """
        self.config_base = base
        """ configerus get key that should contain all tf config """

        self.litmuschaos: LitmusChaos = None
        """LitmusChaos cli handler created in prepare()."""

    # the deep argument is a standard for the info hook
    # pylint: disable=unused-argument
    def info(self, deep: bool = False):
        """Return plugin info in an dict format for debugging."""
        config_loaded = self._environment.config().load(self.config_label)

        info = {
            "config": {
                "label": self.config_label,
                "base": self.config_base,
                "contents": config_loaded.get(self.config_base, default={}),
            }
        }

        return info

    def prepare(self, fixtures: Fixtures = None):
        """Prepare workload prepare.

        Parameters:
        -----------
        fixtures (Fixtures) : a set of fixtures that this workload will use to
            retrieve a kubernetes api client plugin.

        """
        if fixtures is None:
            fixtures = self._environment.fixtures()

        loaded = self._environment.config().load(self.config_label)

        # Validate the config overall using jsonschema
        try:
            loaded.get(self.config_base, validator=LITMUSCHAOS_VALIDATE_TARGET)
        except ValidationError as err:
            raise ValueError("Invalid litmus chaos config received") from err

        kube_client = fixtures.get_plugin(
            plugin_type=METTA_PLUGIN_INTERFACE_ROLE_CLIENT,
            plugin_id=METTA_PLUGIN_ID_KUBERNETES_CLIENT,
        )

        namespace = loaded.get(
            [self.config_base, LITMUSCHAOS_CONFIG_KEY_NAMESPACE],
            default=LITMUSCHAOS_CONFIG_DEFAULT_NAMESPACE,
        )

        version = loaded.get(
            [self.config_base, LITMUSCHAOS_CONFIG_KEY_VERSION],
            default=LITMUSCHAOS_OPERATOR_DEFAULT_VERSION,
        )

        experiments = loaded.get(
            [self.config_base, LITMUSCHAOS_CONFIG_KEY_EXPERIMENTS],
            default=LITMUSCHAOS_CONFIG_DEFAULT_EXPERIMENTS,
        )

        self.litmuschaos = LitmusChaos(
            kube_client=kube_client,
            namespace=namespace,
            version=version,
            experiments=experiments,
        )

    def apply(self):
        """Run the Litmus Chaos experiments."""

    def destroy(self):
        """Remove all litmus chaos components from the cluster."""
