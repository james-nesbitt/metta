"""

Run a Sonobuoy run on a k82 client.

Use this to run the sonobuoy implementation

"""
from typing import Any
import logging

from configerus.loaded import LOADED_KEY_ROOT
from configerus.contrib.jsonschema.validate import (
    PLUGIN_ID_VALIDATE_JSONSCHEMA_SCHEMA_CONFIG_LABEL,
)
from configerus.validator import ValidationError

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.fixtures import Fixtures
from mirantis.testing.metta.client import METTA_PLUGIN_INTERFACE_ROLE_CLIENT
from mirantis.testing.metta_kubernetes import (
    METTA_PLUGIN_ID_KUBERNETES_CLIENT,
    KubernetesApiClientPlugin,
)

from .sonobuoy import (
    Sonobuoy,
    SonobuoyStatus,
    SonobuoyResults,
    SONOBUOY_DEFAULT_RESULTS_PATH,
)

logger = logging.getLogger("workload.sonobuoy")

METTA_PLUGIN_ID_SONOBUOY_WORKLOAD = "metta_sonobuoy_workload"
""" workload plugin_id for the sonobuoy plugin """

SONOBUOY_WORKLOAD_CONFIG_LABEL = "sonobuoy"
""" Configerus label for retrieving sonobuoy config """
SONOBUOY_WORKLOAD_CONFIG_BASE = LOADED_KEY_ROOT
""" Configerus get base for retrieving the default workload config """

SONOBUOY_CONFIG_KEY_MODE = "mode"
""" config key for mode """
SONOBUOY_CONFIG_KEY_KUBERNETESVERSION = "kubernetes.version"
""" config key for kubernetes version """
SONOBUOY_CONFIG_KEY_PLUGINS = "plugin.plugins"
""" config key for what plugins to run """
SONOBUOY_CONFIG_KEY_PLUGINENVS = "plugin.envs"
""" config key for plugin env flags """
SONOBUOY_CONFIG_KEY_RESULTSPATH = "results.path"
""" config key for path to put results """

SONOBUOY_VALIDATE_JSONSCHEMA = {
    "type": "object",
    "properties": {
        "type": {"type": "string"},
        "plugin_id": {"type": "string"},
        "mode": {"type": "string"},
        "kubernetes": {
            "type": "object",
            "properties": {"version": {"type": "string"}},
        },
        "kubernetes_version": {"type": "string"},
        "plugin": {
            "type": "object",
            "properties": {
                "plugins": {"type": "array", "items": {"type": "string"}},
                "plugin_envs": {"type": "array", "items": {"type": "string"}},
            },
        },
    },
    "required": ["mode", "kubernetes"],
}
""" Validation jsonschema for terraform config contents """
SONOBUOY_VALIDATE_TARGET = {
    PLUGIN_ID_VALIDATE_JSONSCHEMA_SCHEMA_CONFIG_LABEL: SONOBUOY_VALIDATE_JSONSCHEMA
}
""" configerus validation target to match the jsonschema config """


class SonobuoyWorkloadPlugin:
    """Workload class for the Sonobuoy"""

    def __init__(
        self,
        environment: Environment,
        instance_id: str,
        label: str = SONOBUOY_WORKLOAD_CONFIG_LABEL,
        base: Any = SONOBUOY_WORKLOAD_CONFIG_BASE,
    ):
        """Initialize workload plugin.

        Parameters:
        -----------
        label (str) : Configerus label for loading config
        base (Any) : configerus base key which should contain all of the config

        """
        self._environment = environment
        """ Environemnt in which this plugin exists """
        self._instance_id = instance_id
        """ Unique id for this plugin instance """

        logger.info("Preparing sonobuoy settings")

        self._config_label = label
        """ configerus load label that should contain all of the config """
        self._config_base = base
        """ configerus get key that should contain all tf config """

        loaded = self._environment.config.load(self._config_label)
        """ get a configerus LoadedConfig for the sonobuoy label """

        # Validate the config overall using jsonschema
        try:
            loaded.get(self._config_base, validator=SONOBUOY_VALIDATE_TARGET)
        except ValidationError as err:
            raise ValueError("Invalid sonobuoy config received") from err

        self._sonobuoy: Sonobuoy = None
        """Sonobuoy cli client."""
        # maybe get this from config?
        self._results_path: str = SONOBUOY_DEFAULT_RESULTS_PATH
        """String path to where to keep the results."""

    # the deep argument is a standard for the info hook
    # pylint: disable=unused-argument
    def info(self, deep: bool = False):
        """Return dict data about this plugin for introspection."""
        loaded = self._environment.config.load(self._config_label)
        """ get a configerus LoadedConfig for the sonobuoy label """
        sonobuoy_config = loaded.get(self._config_base, default={})
        """ load the sonobuoy conifg (e.g. sonobuoy.yml) """

        return {
            "workload": {
                "cncf": sonobuoy_config,
                "required_fixtures": {
                    "kubernetes": {
                        "interface": [METTA_PLUGIN_INTERFACE_ROLE_CLIENT],
                        "plugin_id": METTA_PLUGIN_ID_KUBERNETES_CLIENT,
                    }
                },
            }
        }

    def prepare(self, fixtures: Fixtures = None):
        """Create a workload instance from a set of fixtures.

        Parameters:
        -----------
        fixtures (Fixtures) : a set of fixtures that this workload will use to
            retrieve a kubernetes api client plugin.

        """
        if fixtures is None:
            fixtures = self._environment.fixtures

        loaded = self._environment.config.load(self._config_label)
        """ get a configerus LoadedConfig for the sonobuoy label """

        # Validate the config overall using jsonschema
        try:
            loaded.get(self._config_base, validator=SONOBUOY_VALIDATE_TARGET)
        except ValidationError as err:
            raise ValueError("Invalid sonobuoy config received") from err

        kubeclient: KubernetesApiClientPlugin = fixtures.get_plugin(
            plugin_id=METTA_PLUGIN_ID_KUBERNETES_CLIENT,
        )

        mode = loaded.get([self._config_base, SONOBUOY_CONFIG_KEY_MODE])
        kubernetes_version = loaded.get(
            [self._config_base, SONOBUOY_CONFIG_KEY_KUBERNETESVERSION], default=""
        )
        plugins = loaded.get(
            [self._config_base, SONOBUOY_CONFIG_KEY_PLUGINS], default=[]
        )
        plugin_envs = loaded.get(
            [self._config_base, SONOBUOY_CONFIG_KEY_PLUGINENVS], default=[]
        )

        self._results_path: str = loaded.get(
            [self._config_base, SONOBUOY_CONFIG_KEY_RESULTSPATH],
            default=SONOBUOY_DEFAULT_RESULTS_PATH,
        )

        self._sonobuoy = Sonobuoy(
            api_client=kubeclient,
            mode=mode,
            kubernetes_version=kubernetes_version,
            plugins=plugins,
            plugin_envs=plugin_envs,
            results_path=self._results_path,
        )

    # These are work for this scenario
    # pylint: disable=arguments-differ
    def apply(self, wait: bool = True):
        """Run sonobuoy."""
        logger.info("Starting Sonobuoy run")
        self._sonobuoy.run(wait=wait)

    def status(self) -> SonobuoyStatus:
        """Retrieve Sonobuoy status return."""
        return self._sonobuoy.status()

    def retrieve(self) -> SonobuoyResults:
        """Retrieve sonobuoy results."""
        logger.debug("retrieving sonobuoy results")
        return self._sonobuoy.retrieve()

    def destroy(self, wait: bool = True):
        """Delete sonobuoy resources."""
        logger.debug("removing sonobuoy infrastructure")
        self._sonobuoy.destroy(wait=wait)
