"""

Run a Sonobuoy run on a k82 client.

Use this to run the sonobuoy implementation

"""
from typing import Any, List, Dict
import logging

import yaml

from configerus.loaded import Loaded, LOADED_KEY_ROOT
from configerus.contrib.jsonschema.validate import (
    PLUGIN_ID_VALIDATE_JSONSCHEMA_SCHEMA_CONFIG_LABEL,
)
from configerus.validator import ValidationError

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.fixture import Fixtures
from mirantis.testing.metta.client import METTA_PLUGIN_INTERFACE_ROLE_CLIENT
from mirantis.testing.metta_kubernetes import (
    METTA_PLUGIN_ID_KUBERNETES_CLIENT,
    KubernetesApiClientPlugin,
)

from .client import METTA_SONOBUOY_CLIENT_PLUGIN_ID, SonobuoyClientPlugin
from .plugin import Plugin
from .sonobuoy import (
    SONOBUOY_DEFAULT_RESULTS_PATH,
)
from .results import (
    SonobuoyStatus,
    SonobuoyResults,
)

logger = logging.getLogger("workload.sonobuoy")

METTA_SONOBUOY_WORKLOAD_PLUGIN_ID = "metta_sonobuoy_workload"
""" workload plugin_id for the sonobuoy plugin """

SONOBUOY_WORKLOAD_CONFIG_LABEL = "sonobuoy"
""" Configerus label for retrieving sonobuoy config """
SONOBUOY_WORKLOAD_CONFIG_BASE = LOADED_KEY_ROOT
""" Configerus get base for retrieving the default workload config """

SONOBUOY_CONFIG_KEY_MODE = "mode"
""" config key for mode """
SONOBUOY_CONFIG_KEY_KUBERNETESVERSION = "kubernetes.version"
""" config key for kubernetes version """
SONOBUOY_CONFIG_KEY_PLUGINS = "plugins"
""" config key for what plugins to run """
SONOBUOY_CONFIG_KEY_PLUGINDEF = "definition"
""" config key for plugin definition """
SONOBUOY_CONFIG_KEY_PLUGINPATH = "path"
""" config key for plugin file path """
SONOBUOY_CONFIG_KEY_PLUGINENVS = "envs"
""" config key for plugin env vars"""
SONOBUOY_CONFIG_KEY_RESULTSPATH = "results.path"
""" config key for path to put results """

# THIS IS OUT OF DATSE
SONOBUOY_VALIDATE_JSONSCHEMA = {
    "type": "object",
    "properties": {"plugins": {"$ref": "#/definitions/plugin"}},
    "definitions": {
        "plugin": {
            "type": "object",
            "properties": {
                # Optionally provide a plugin path
                "path": {"type": "string"},
                # Optionally provide a definition
                "definition": {"type": "object"},
                # dict of plugin env variables.
                "envs": {"$ref": "string"},
            },
        }
    },
}
""" Validation jsonschema for terraform config contents """
SONOBUOY_VALIDATE_TARGET = {
    PLUGIN_ID_VALIDATE_JSONSCHEMA_SCHEMA_CONFIG_LABEL: SONOBUOY_VALIDATE_JSONSCHEMA
}
""" configerus validation target to match the jsonschema config """


class SonobuoyWorkloadPlugin:
    """Workload class for the Sonobuoy."""

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
        self._environment: Environment = environment
        """ Environemnt in which this plugin exists """
        self._instance_id: str = instance_id
        """ Unique id for this plugin instance """

        logger.info("Preparing sonobuoy settings")

        self._config_label: str = label
        """ configerus load label that should contain all of the config """
        self._config_base: str = base
        """ configerus get key that should contain all tf config """

        self.fixtures: Fixtures = Fixtures()
        """This plugin creates fixtures, so they are tracked here."""

        # go for early declarative testing to the plugin.
        try:
            self.prepare()
        # pylint: disable=broad-except
        except Exception:
            logger.debug("not able to early prepare sonobuoy.")

    # the deep argument is a standard for the info hook
    # pylint: disable=unused-argument
    def info(self, deep: bool = False):
        """Return dict data about this plugin for introspection."""
        # get a configerus LoadedConfig for the sonobuoy label
        loaded: Loaded = self._environment.config().load(self._config_label)
        # load the sonobuoy conifg (e.g. sonobuoy.yml)
        sonobuoy_config: Dict[str, Any] = loaded.get(self._config_base, default={})

        return {
            "config": {"label": self._config_label, "base": self._config_base},
            "workload": {
                "config": sonobuoy_config,
                "required_fixtures": {
                    "kubernetes": {
                        "interface": [METTA_PLUGIN_INTERFACE_ROLE_CLIENT],
                        "plugin_id": METTA_PLUGIN_ID_KUBERNETES_CLIENT,
                    }
                },
                "run": {"args": loaded.get([self._config_base, "run"], default="NONE")},
            },
        }

    def prepare(self, fixtures: Fixtures = None):
        """Create a workload instance from a set of fixtures.

        Parameters:
        -----------
        fixtures (Fixtures) : a set of fixtures that this workload will use to
            retrieve a kubernetes api client plugin.

        """
        if fixtures is None:
            fixtures = self._environment.fixtures()

        # Retrieve and Validate the config overall using jsonschema
        try:
            # get a configerus LoadedConfig for the sonobuoy label
            loaded = self._environment.config().load(
                self._config_label, validator=SONOBUOY_VALIDATE_TARGET
            )
        except ValidationError as err:
            raise ValueError("Invalid sonobuoy config received") from err

        # We need to discover all of the plugins to run.
        #
        # For plugins with inline definitions, we need to create file definitions
        # to pass to sonobuoy.
        resources_path: str = loaded.get([self._config_base, "resources.path"], default="./")
        resources_prefix: str = loaded.get(
            [self._config_base, "resources.prefix"], default="sonobuoy-plugin-"
        )

        plugins: List[Plugin] = []
        for plugin_id in loaded.get(
            [self._config_base, SONOBUOY_CONFIG_KEY_PLUGINS], default={}
        ).keys():

            plugin_envs = loaded.get(
                [
                    self._config_base,
                    SONOBUOY_CONFIG_KEY_PLUGINS,
                    plugin_id,
                    SONOBUOY_CONFIG_KEY_PLUGINENVS,
                ],
                default=plugin_id,
            )

            # plugin_def gives us a plugin definition which defines what we pass
            # to sonobuoy using the -p flag.
            #
            # If a plugin def is missing then plugin_id is used.
            #
            # It can be one of three types:
            # 1. a core plugin id like 'e2e'
            # 2. a path to a plugin yml file which defines a plugin.
            # 3. an object which defines the plugin conf which will be written
            #    to a yaml file.
            plugin_def = loaded.get(
                [
                    self._config_base,
                    SONOBUOY_CONFIG_KEY_PLUGINS,
                    plugin_id,
                    SONOBUOY_CONFIG_KEY_PLUGINDEF,
                ],
                default="",
            )
            plugin_path = loaded.get(
                [
                    self._config_base,
                    SONOBUOY_CONFIG_KEY_PLUGINS,
                    plugin_id,
                    SONOBUOY_CONFIG_KEY_PLUGINPATH,
                ],
                default="",
            )

            if plugin_def:
                # here we received a plugin definition which we must write to
                # a file.
                if not plugin_path:
                    plugin_path = resources_path + resources_prefix + plugin_id + ".yml"

                with open(plugin_path, "w") as plugin_file:
                    yaml.dump(plugin_def, plugin_file, encoding="utf-8")
                plugin_def = plugin_path

                plugins.append(
                    Plugin(plugin_id=plugin_id, plugin_def=plugin_path, envs=plugin_envs)
                )
                continue

            if plugin_path:
                plugins.append(
                    Plugin(plugin_id=plugin_id, plugin_def=plugin_path, envs=plugin_envs)
                )
                continue

            plugins.append(Plugin(plugin_id=plugin_id, plugin_def=plugin_id, envs=plugin_envs))

        # String path to where to keep the results.
        # maybe get this from config?
        results_path: str = loaded.get(
            [self._config_base, SONOBUOY_CONFIG_KEY_RESULTSPATH],
            default=SONOBUOY_DEFAULT_RESULTS_PATH,
        )

        kubeclient: KubernetesApiClientPlugin = fixtures.get_plugin(
            plugin_id=METTA_PLUGIN_ID_KUBERNETES_CLIENT,
        )

        client_fixture = self._environment.new_fixture(
            plugin_id=METTA_SONOBUOY_CLIENT_PLUGIN_ID,
            instance_id=self.client_instance_id(),
            priority=70,
            arguments={
                "kubeclient": kubeclient,
                "plugins": plugins,
                "results_path": results_path,
            },
            labels={
                "container": "plugin",
                "environment": self._environment.instance_id(),
                "parent_plugin_id": METTA_SONOBUOY_WORKLOAD_PLUGIN_ID,
                "parent_instance_id": self._instance_id,
            },
            replace_existing=True,
        )
        # keep this fixture attached to the workload to make it retrievable.
        self.fixtures.add(client_fixture, replace_existing=True)

    # These are work for this scenario
    # pylint: disable=arguments-differ
    def apply(self, wait: bool = True):
        """Run sonobuoy."""
        logger.info("Starting Sonobuoy run")

        # Retrieve and Validate the config overall using jsonschema
        try:
            # get a configerus LoadedConfig for the sonobuoy label
            loaded = self._environment.config().load(self._config_label)
        except ValidationError as err:
            raise ValueError("Invalid sonobuoy config received") from err

        # Get the run time arguments
        run_args: List[str] = []
        for (key, value) in loaded.get([self._config_base, "run"], default={}).items():
            run_args.append(f"--{key}={value}")

        return self.get_client_plugin().run(wait=wait, run_args=run_args)

    def status(self) -> SonobuoyStatus:
        """Retrieve Sonobuoy status return."""
        return self.get_client_plugin().status()

    def retrieve(self) -> SonobuoyResults:
        """Retrieve sonobuoy results."""
        logger.debug("retrieving sonobuoy results")
        return self.get_client_plugin().retrieve()

    def destroy(self, wait: bool = True):
        """Delete sonobuoy resources."""
        logger.debug("removing sonobuoy infrastructure")
        self.get_client_plugin().delete(wait=wait)

    def client_instance_id(self) -> str:
        """Return the instanceid for the child client plugin."""
        return f"{self._instance_id}-{METTA_SONOBUOY_CLIENT_PLUGIN_ID}"

    def get_client_plugin(self) -> SonobuoyClientPlugin:
        """Retrieve the client plugin if we can."""
        try:
            return self.fixtures.get_plugin(plugin_id=METTA_SONOBUOY_CLIENT_PLUGIN_ID)
        except KeyError as err:
            # Prepare was likely not run yet.
            raise RuntimeError(
                "Sonobuoy workload cannot find a client plugin. We "
                "likely have not created it yet. Did you run the "
                "prepare() method yet?"
            ) from err
