"""

Launchpad metta provisioner plugin.

Provisioner/Install Mirantis products onto an existing cluster using a
Launchpad client plugin.  This is effectively a provisioner style wrapper
for the client plugin, which this plugin will create from provisioner
configuration.

"""
import os.path
import logging
from typing import Any, List, Dict
import yaml

from configerus.loaded import LOADED_KEY_ROOT
from configerus.contrib.jsonschema.validate import (
    PLUGIN_ID_VALIDATE_JSONSCHEMA_SCHEMA_CONFIG_LABEL,
)
from configerus.validator import ValidationError

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.fixture import Fixtures

from .client import (
    METTA_LAUNCHPAD_CLIENT_PLUGIN_ID,
    LaunchpadClientPlugin,
)
from .launchpad import (
    METTA_LAUNCHPAD_CLI_CONFIG_FILE_DEFAULT,
    METTA_LAUNCHPADCLIENT_WORKING_DIR_DEFAULT,
)

logger = logging.getLogger("metta_launchpad:provisioner")

METTA_LAUNCHPAD_PROVISIONER_PLUGIN_ID = "metta_launchpad_provisioner"
""" Metta plugin_id for the launchpad provisioner plugin """

METTA_LAUNCHPAD_CONFIG_LABEL = "launchpad"
"""Launchpad config label for configuration"""
METTA_LAUNCHPAD_CLIENT_SYSTEMS_KEY = "systems"
"""If provided, this config key provide a dictionary of configuration of client system plugins."""
METTA_LAUNCHPAD_CONFIG_ROOT_PATH_KEY = "root.path"
"""Config key for a base file path that should be used for any relative paths"""
METTA_LAUNCHPAD_CONFIG_KEY = "config"
"""Which config key will provide the launchpad yml"""
METTA_LAUNCHPAD_CLI_CONFIG_FILE_KEY = "config_file"
"""Launchpad config cli key to tell us where to put the launchpad yml file"""
METTA_LAUNCHPAD_CLI_WORKING_DIR_KEY = "working_dir"
"""Launchpad config cli configuration working dir key """
METTA_LAUNCHPAD_CLI_CLUSTEROVERRIDE_KEY = "cluster_name"
"""If provided, this config key will override a cluster name pulled from yaml"""
METTA_LAUNCHPAD_CLI_OPTIONS_KEY = "cli"
"""If provided, these will be passed to the launchpad client to be used on all operations"""

METTA_LAUNCHPAD_VALIDATE_JSONSCHEMA = {
    "type": "object",
    "properties": {
        "config": {
            "type": ["object", "null"],
        },
        "systems": {
            "type": "object",
            "properties": {
                "mirantis_mke_client": {
                    "type": "object",
                    "properties": {
                        "accesspoint": {"type": ["string", "null"]},
                        "username": {"type": ["string", "null"]},
                        "password": {"type": ["string", "null"]},
                        "client_bundle_root": {"type": ["string", "null"]},
                    },
                },
                "mirantis_msr_client": {
                    "type": "object",
                    "properties": {
                        "accesspoint": {"type": ["string", "null"]},
                        "username": {"type": ["string", "null"]},
                        "password": {"type": ["string", "null"]},
                    },
                },
            },
        },
        "cli": {
            "accept-license": {"type": "bool"},
            "disable-telemetry": {"type": "bool"},
        },
        "config_file": {"type": "string"},
        "working_dir": {"type": "string"},
    },
    "required": ["config_file"],
}
""" Validation jsonschema for Launchpad config contents """
METTA_LAUNCHPAD_PROVISIONER_VALIDATE_TARGET = {
    PLUGIN_ID_VALIDATE_JSONSCHEMA_SCHEMA_CONFIG_LABEL: METTA_LAUNCHPAD_VALIDATE_JSONSCHEMA
}
""" configerus validation target to match validate Launchpad config """

METTA_LAUNCHPAD_CONFIG_VALIDATE_JSONSCHEMA = {
    "type": "object",
    "properties": {
        "apiVersion": {"type": "string"},
        "kind": {"type": "string"},
        "hosts": {"type": "array", "items": {"type": "object"}},
        "spec": {
            "type": "object",
            "properties": {
                "mcr": {"type": "object"},
                "mke": {"type": "object"},
                "msr": {"type": "object"},
            },
            "required": ["mcr", "mke"],
        },
    },
    "required": ["apiVersion", "kind", "spec"],
}
""" Validation jsonschema for launchpad configuration """
METTA_LAUNCHPAD_CONFIG_VALIDATE_TARGET = {
    PLUGIN_ID_VALIDATE_JSONSCHEMA_SCHEMA_CONFIG_LABEL: METTA_LAUNCHPAD_CONFIG_VALIDATE_JSONSCHEMA
}
""" configerus jsonschema validation target for launchpad config """


# pylint: disable=too-many-instance-attributes
class LaunchpadProvisionerPlugin:
    """Launchpad provisioner class.

    Use this to provision a system using Mirantis launchpad

    """

    def __init__(
        self,
        environment: Environment,
        instance_id: str,
        label: str = METTA_LAUNCHPAD_CONFIG_LABEL,
        base: Any = LOADED_KEY_ROOT,
    ):
        """Configure a new Launchpad provisioner plugin instance."""
        self._environment: Environment = environment
        """ Environemnt in which this plugin exists """
        self._instance_id: str = instance_id
        """ Unique id for this plugin instance """

        self._config_label = label
        """ configerus load label that should contain all of the config """
        self._config_base = base
        """ configerus get key that should contain all tf config """

        self.fixtures = Fixtures()
        """ keep a collection of fixtures that this provisioner creates """

        # attempt to be declarative and make the client plugin in case the
        # terraform chart has already been run.
        try:
            # Make the child client plugin.
            self.make_fixtures()

        # dont' block the construction on an exception
        # pylint: disable=broad-except
        except Exception:
            pass

    def info(self, deep: bool = False) -> Dict[str, Any]:
        """Get info about the plugin.

        Returns:
        --------
        Dict of introspective information about this plugin_info

        """
        # Loaded plugin configuration
        launchpad_config_loaded = self._environment.config().load(self._config_label)

        return {
            "plugin": {
                "config_label": self._config_label,
                "config_base": self._config_base,
            },
            "config": {
                "working_dir": launchpad_config_loaded.get(
                    [self._config_base, METTA_LAUNCHPAD_CLI_WORKING_DIR_KEY], default="MISSING"
                ),
                "root_path": launchpad_config_loaded.get(
                    [self._config_base, METTA_LAUNCHPAD_CONFIG_ROOT_PATH_KEY], default="NONE"
                ),
                "config_file": launchpad_config_loaded.get(
                    [self._config_base, METTA_LAUNCHPAD_CLI_CONFIG_FILE_KEY], default="MISSING"
                ),
                "cli_options": launchpad_config_loaded.get(
                    [self._config_base, METTA_LAUNCHPAD_CLI_OPTIONS_KEY], default="NONE"
                ),
            },
            "client": self._get_client_plugin().info(deep=deep),
        }

    # pylint: disable=no-self-use
    def prepare(self):
        """Prepare the provisioning cluster for install.

        We ignore this.

        """
        logger.info("Running Launchpad Prepare().  Launchpad has no prepare stage.")

    def apply(self, debug: bool = False):
        """Bring a cluster up.

        Not that we re-write the yaml file as it may depend on config which was not
        available when this object was first constructed.

        Raises:
        -------
        ValueError if the object has been configured (prepare) with config that
            doesn't work, or if the backend doesn't give valid yml

        Exception if launchpad fails.

        """
        logger.info("Using launchpad to install products onto backend cluster")
        self._write_launchpad_yml()
        self.make_fixtures()  # we wouldn't need this if we could update the systems
        self._get_client_plugin().apply(debug=debug)

    def destroy(self):
        """Ask the client to remove installed resources."""
        if self._has_launchpad_yml():
            logger.info("Using launchpad to remove installed products from the backend cluster")
            self._get_client_plugin().reset()
            self._rm_launchpad_yml()

    # ----- CLUSTER INTERACTION -----

    def _has_launchpad_yml(self) -> bool:
        """Check if the launchpad yml file exists."""
        # Loaded configerus config for the plugin. Ready for .get().
        plugin_config = self._environment.config().load(self._config_label)

        config_file: str = plugin_config.get(
            [self._config_base, METTA_LAUNCHPAD_CLI_CONFIG_FILE_KEY],
            default=METTA_LAUNCHPAD_CLI_CONFIG_FILE_DEFAULT,
        )
        return bool(config_file) and os.path.exists(config_file)

    def _write_launchpad_yml(self):
        """Write config contents to a yaml file for launchpad."""
        self._rm_launchpad_yml()

        # load and validation all of the launchpad configuration.
        launchpad_loaded = self._environment.config().load(
            self._config_label,
            validator=METTA_LAUNCHPAD_PROVISIONER_VALIDATE_TARGET,
            force_reload=True,
        )

        # load all of the launchpad configuration, force a reload to get up to date contents
        config_contents: Dict[str, Any] = launchpad_loaded.get(
            [self._config_base, METTA_LAUNCHPAD_CONFIG_KEY],
            validator=METTA_LAUNCHPAD_CONFIG_VALIDATE_TARGET,
        )

        # decide on a path for the runtime launchpad.yml file
        config_path: str = os.path.realpath(
            launchpad_loaded.get(
                [self._config_base, METTA_LAUNCHPAD_CLI_CONFIG_FILE_KEY],
                default=METTA_LAUNCHPAD_CLI_CONFIG_FILE_DEFAULT,
            )
        )

        # Our launchpad config differs slightly from the schema that launchpad
        # consumes, so we need a small conversion
        config_contents = self._convert_launchpad_config_to_file_format(config_contents)

        # write the launchpad output to our yaml file target (after creating the path)
        logger.debug(
            "Updating launchpad yaml file: %s =>/n%s",
            config_path,
            yaml.dump(config_contents),
        )
        with open(config_path, "w", encoding="utf8") as config_file_object:
            yaml.dump(config_contents, config_file_object)

    def _rm_launchpad_yml(self):
        """Update config and write the cfg and inventory files."""
        # Loaded configerus config for the plugin. Ready for .get().
        plugin_config = self._environment.config().load(self._config_label)

        config_file: str = plugin_config.get(
            [self._config_base, METTA_LAUNCHPAD_CLI_CONFIG_FILE_KEY],
            default=METTA_LAUNCHPAD_CLI_CONFIG_FILE_DEFAULT,
        )
        if config_file and os.path.exists(config_file):
            logger.debug("Launchpad provisioner removing created files.")
            os.remove(config_file)

    def make_fixtures(self):
        """Make the client plugin for terraform interaction."""
        try:
            # load and validation all of the launchpad configuration.
            launchpad_config_loaded = self._environment.config().load(
                self._config_label,
                validator=METTA_LAUNCHPAD_PROVISIONER_VALIDATE_TARGET,
                force_reload=True,
            )
        except ValidationError as err:
            raise ValueError("Launchpad config failed validation.") from err

        # if launchpad needs to be run in a certain path, set it with this config
        working_dir: str = launchpad_config_loaded.get(
            [self._config_base, METTA_LAUNCHPAD_CLI_WORKING_DIR_KEY],
            default=METTA_LAUNCHPADCLIENT_WORKING_DIR_DEFAULT,
        )

        # decide on a path for the runtime launchpad.yml file
        config_file: str = launchpad_config_loaded.get(
            [self._config_base, METTA_LAUNCHPAD_CLI_CONFIG_FILE_KEY],
            default=METTA_LAUNCHPAD_CLI_CONFIG_FILE_DEFAULT,
        )
        # List of launchpad cli options to pass to the client for all operations.
        cli_options: Dict[str, Any] = launchpad_config_loaded.get(
            [self._config_base, METTA_LAUNCHPAD_CLI_OPTIONS_KEY], default={}
        )
        # List of systems that the client should configure for children plugins.
        systems: Dict[str, Dict[str, Any]] = launchpad_config_loaded.get(
            [self._config_base, METTA_LAUNCHPAD_CLIENT_SYSTEMS_KEY], default={}
        )

        fixture = self._environment.new_fixture(
            plugin_id=METTA_LAUNCHPAD_CLIENT_PLUGIN_ID,
            instance_id=self.client_instance_id(),
            priority=70,
            arguments={
                "config_file": config_file,
                "working_dir": working_dir,
                "cli_options": cli_options,
                "systems": systems,
            },
            labels={
                "parent_plugin_id": METTA_LAUNCHPAD_PROVISIONER_PLUGIN_ID,
                "parent_instance_id": self._instance_id,
            },
            replace_existing=True,
        )
        # keep this fixture attached to the workload to make it retrievable.
        self.fixtures.add(fixture, replace_existing=True)

    def client_instance_id(self) -> str:
        """Construct an instanceid for the child client plugin."""
        return f"{self._instance_id}-{METTA_LAUNCHPAD_CLIENT_PLUGIN_ID}"

    def _get_client_plugin(self) -> LaunchpadClientPlugin:
        """Retrieve the client plugin if we can."""
        try:
            return self.fixtures.get_plugin(plugin_id=METTA_LAUNCHPAD_CLIENT_PLUGIN_ID)
        except KeyError as err:
            raise RuntimeError(
                "Launchpad provisioner cannot find its client plugin, and "
                "cannot process any client actions.  Was a client created?"
            ) from err

    def _convert_launchpad_config_to_file_format(self, config):
        """Convert our launchpad config to the schema that launchpad uses."""
        # 1 discover the hosts counts
        hosts = []
        managers = []
        workers = []
        msrs = []
        for host in config["spec"]["hosts"]:
            hosts.append(host)
            if host["role"] == "manager":
                managers.append(host)
            if host["role"] == "worker":
                workers.append(host)
            if host["role"] == "msr":
                msrs.append(host)

        # convert install flags and update flags to lists from dicts
        def dtol(dic):
            """Convert dict flags to lists."""
            items: List[str] = []
            for key, value in dic.items():
                if value is True:
                    items.append(f"--{key}")
                else:
                    items.append(f"--{key}={value}")
            return items

        try:
            config["spec"]["mke"]["installFlags"] = dtol(config["spec"]["mke"]["installFlags"])
        except KeyError:
            pass
        try:
            config["spec"]["mke"]["upgradeFlags"] = dtol(config["spec"]["mke"]["upgradeFlags"])
        except KeyError:
            pass
        try:
            config["spec"]["msr"]["installFlags"] = dtol(config["spec"]["msr"]["installFlags"])
        except KeyError:
            pass
        try:
            config["spec"]["msr"]["upgradeFlags"] = dtol(config["spec"]["msr"]["upgradeFlags"])
        except KeyError:
            pass

        # If no msrs, then drop the msr block and force the type.
        if len(msrs) == 0:
            config["kind"] = "mke"
            config["spec"].pop("msr")

        return config
