"""

Metta provisioner plugin for testkit.

A provisioner plugin that uses testkit to create infra
and optionally to install either kubernetes or Mirantis
MKE/MSR onto the infra.

"""
import logging
import os
from typing import Any, Dict

import yaml

from configerus.loaded import LOADED_KEY_ROOT
from configerus.contrib.jsonschema.validate import (
    PLUGIN_ID_VALIDATE_JSONSCHEMA_SCHEMA_CONFIG_LABEL,
)
from configerus.validator import ValidationError

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.fixture import Fixtures

from .client import TestkitClientPlugin, METTA_TESTKIT_CLIENT_PLUGIN_ID
from .testkit import TESTKITCLIENT_CLI_CONFIG_FILE_DEFAULT

logger = logging.getLogger("testkit.provisioner")

METTA_TESTKIT_PROVISIONER_PLUGIN_ID = "metta_testkit_provisioner"
""" Metta plugin id for testkit provisioner plugins """

TESTKIT_PROVISIONER_CONFIG_LABEL = "testkit"
"""Configerus config load label for accessing provisioner config."""
TESTKIT_PROVISIONER_CONFIG_BASE = LOADED_KEY_ROOT
""" configerus get base-key for accessing testkit provisioner config """

TESTKIT_CONFIG_KEY_SYSTEMNAME = "system_name"
""" config key to find the system name """
TESTKIT_CONFIG_KEY_SYSTEMS = "systems"
""" config key to find the set of systems installed by testkit """
TESTKIT_CONFIG_KEY_CREATE_OPTIONS = "options.create"
""" config key to find where the testkit create options """
TESTKIT_CONFIG_KEY_CONFIG = "config"
""" config key to find where to put the testkit config file data/contents """
TESTKIT_CONFIG_KEY_INSTANCES = "instances"
""" config key to find what instances to spec out (build) """
TESTKIT_CONFIG_KEY_CONFIGFILE = "config_file"
""" config key to find where to put the testkit config file """
TESTKIT_CONFIG_DEFAULT_CONFIGFILE = TESTKITCLIENT_CLI_CONFIG_FILE_DEFAULT
""" default value for where to put the testkit config file """

TESTKIT_CLIENT_SYSTEMS_KEY = "systems"
""" If provided, this config key provide a dictionary of configuration of client system plugins. """

TESTKIT_CONFIG_VALIDATE_JSONSCHEMA = {
    "type": "object",
    "properties": {
        "ucp": {"type": "object"},
        "dtr": {"type": "object"},
        "": {"type": "object"},
    },
    "required": [],
}
""" Validation jsonschema for testkit configuration for testkit yaml files """
TESTKIT_CONFIG_VALIDATE_TARGET = {
    PLUGIN_ID_VALIDATE_JSONSCHEMA_SCHEMA_CONFIG_LABEL: TESTKIT_CONFIG_VALIDATE_JSONSCHEMA
}
""" configerus jsonschema validation target for testkit config file """

TESTKIT_PROV_CONFIG_VAL_JSONSCHEMA = {
    "type": "object",
    "properties": {
        "opts": {"type": "object"},
        "config": TESTKIT_CONFIG_VALIDATE_JSONSCHEMA,
    },
    "required": [],
}
""" Validation jsonschema for provisioner configuration """
TESTKIT_PROV_CONFIG_VALIDATE_TARGET = {
    PLUGIN_ID_VALIDATE_JSONSCHEMA_SCHEMA_CONFIG_LABEL: TESTKIT_PROV_CONFIG_VAL_JSONSCHEMA
}
""" configerus jsonschema validation target for the provisioner plugin """


class TestkitProvisionerPlugin:
    """Testkit provisioner plugin.

    Provisioner plugin that allows control of and interaction with a testkit
    cluster.

    ## Requirements

    1. this plugin uses subprocess to call a testkit binary, so you have to
       install testkit in the environment

    ## Usage

    @TODO

    """

    def __init__(
        self,
        environment,
        instance_id,
        label: str = TESTKIT_PROVISIONER_CONFIG_LABEL,
        base: Any = TESTKIT_PROVISIONER_CONFIG_BASE,
    ):
        """Initialize Testkit provisioner.

        Parameters:
        -----------
        environment (Environment) : metta environment object that this plugin
            is attached.
        instance_id (str) : label for this plugin instances.

        label (str) : config load label for plugin configuration.
        base (str) : config base for loaded config for plugin configuration.

        """
        self._environment: Environment = environment
        """ Environemnt in which this plugin exists """
        self._instance_id: str = instance_id
        """ Unique id for this plugin instance """

        self._config_label = label
        """ configerus load label that should contain all of the config """
        self._config_base = base

        self.fixtures = Fixtures()
        """This object makes and keeps track of fixtures for MKE/MSR clients."""

        try:
            self._write_config_file()
            self.make_fixtures()
            # pylint: disable= broad-except
        except Exception as err:
            # there are many reasons this can fail, and we just want to
            # see if we can get fixtures early.
            # No need to ask forgiveness for this one.
            logger.debug("Could not make initial fixtures: %s", err)

    # the deep argument is a standard for the info hook
    # pylint: disable=unused-argument
    def info(self, deep: bool = False) -> Dict[str, Any]:
        """Get info about a provisioner plugin."""
        testkit_config = self._environment.config().load(self._config_label)

        return {
            "plugin": {
                "config": {
                    "config_label": self._config_label,
                    "config_base": self._config_base,
                },
                "config_file": testkit_config.get(
                    [self._config_base, TESTKIT_CONFIG_KEY_CONFIGFILE],
                    default="MISSING",
                ),
                "working_dir": testkit_config.get(
                    [self._config_base, TESTKIT_CONFIG_KEY_SYSTEMNAME], default="MISSING"
                ),
                "systems": testkit_config.get(
                    [self._config_base, TESTKIT_CONFIG_KEY_SYSTEMNAME],
                    default="MISSING",
                ),
            },
            "client": self._get_client_plugin().info(deep=deep),
        }

    def prepare(self):
        """Prepare any needed resources.

        We don't create the testkit file here so that it is created as late as
        possible.  This allows more options for dynamic config sources in the
        testkit config.

        """
        # Make sure that we are running on up to date config
        self._write_config_file()
        self.make_fixtures()

    def apply(self):
        """Create the testkit yaml file and run testkit to create a cluster."""
        # Make sure that we are running on up to date config
        self._write_config_file()
        self.make_fixtures()

        testkit_config = self._environment.config().load(self._config_label, force_reload=True)
        """ load the plugin configuration so we can retrieve options """
        opts = testkit_config.get(
            [self._config_base, TESTKIT_CONFIG_KEY_CREATE_OPTIONS], default={}
        )
        """ retrieve testkit client options from config """
        opt_list = []
        for key, value in opts.items():
            if isinstance(value, str):
                opt_list.append(f'--{key}="{value}"')
            else:
                opt_list.append(f"--{key}={value}")

        # run the testkit client command to provisioner the cluster
        self._get_client_plugin().create(opts=opt_list)

    def destroy(self):
        """Destroy any created resources."""
        # run the testkit client command to provisioner the cluster
        self._get_client_plugin().destroy()
        self._rm_config_file()

    def _write_config_file(self):
        """Write the config file for testkit."""
        try:
            # load all of the testkit configuration, force a reload to get up to date contents
            testkit_config = self._environment.config().load(self._config_label, force_reload=True)
            config = testkit_config.get(
                [self._config_base, TESTKIT_CONFIG_KEY_CONFIG],
                validator=TESTKIT_CONFIG_VALIDATE_TARGET,
            )
            """ config source of launchpad yaml """
        except KeyError as err:
            raise ValueError("Could not find launchpad configuration from config.") from err
        except ValidationError as err:
            raise ValueError("Launchpad config failed validation") from err

        config_file = testkit_config.get(
            [self._config_base, TESTKIT_CONFIG_KEY_CONFIGFILE],
            default=TESTKIT_CONFIG_DEFAULT_CONFIGFILE,
        )
        """ config_file value from plugin configuration """

        # write the configto our yaml file target (creating the path)
        os.makedirs(os.path.dirname(os.path.realpath(config_file)), exist_ok=True)
        with open(os.path.realpath(config_file), "w", encoding="utf8") as file:
            yaml.dump(config, file)

    def _rm_config_file(self):
        """Remove the written config file."""
        testkit_config = self._environment.config().load(self._config_label)
        config_file = testkit_config.get(
            [self._config_base, TESTKIT_CONFIG_KEY_CONFIGFILE],
            default=TESTKIT_CONFIG_DEFAULT_CONFIGFILE,
        )
        if os.path.isfile(config_file):
            os.remove(config_file)

    def make_fixtures(self):
        """Make related fixtures from a testkit installation.

        Creates:
        --------

        Testkit client : a client for interaction with the teskit cli

        """
        testkit_config = self._environment.config().load(self._config_label, force_reload=True)
        """ load the plugin configuration so we can retrieve options """

        try:
            testkit_config = self._environment.config().load(self._config_label, force_reload=True)
            """ loaded plugin configuration label """
        except KeyError as err:
            raise ValueError("Testkit plugin configuration did not have any config") from err

        system_name = testkit_config.get([self._config_base, TESTKIT_CONFIG_KEY_SYSTEMNAME])
        """ hat will testkit call the system """

        # instances = testkit_config.get([self._config_base, TESTKIT_CONFIG_KEY_INSTANCES])
        # """ what instances to create """

        config_file = testkit_config.get(
            [self._config_base, TESTKIT_CONFIG_KEY_CONFIGFILE],
            default=TESTKIT_CONFIG_DEFAULT_CONFIGFILE,
        )
        """ config_file value from plugin configuration """

        systems = testkit_config.get(
            [self._config_base, TESTKIT_CONFIG_KEY_SYSTEMS],
            default={},
        )

        fixture = self._environment.new_fixture(
            plugin_id=METTA_TESTKIT_CLIENT_PLUGIN_ID,
            instance_id=self.client_instance_id(),
            priority=70,
            arguments={
                "config_file": config_file,
                "system_name": system_name,
                "systems": systems,
            },
            labels={
                "parent_plugin_id": METTA_TESTKIT_PROVISIONER_PLUGIN_ID,
                "parent_instance_id": self._instance_id,
            },
            replace_existing=True,
        )
        # keep this fixture attached to the workload to make it retrievable.
        self.fixtures.add(fixture, replace_existing=True)

    def client_instance_id(self) -> str:
        """Construct an instanceid for the child client plugin."""
        return f"{self._instance_id}-{METTA_TESTKIT_CLIENT_PLUGIN_ID}"

    def _get_client_plugin(self) -> TestkitClientPlugin:
        """Retrieve the client plugin if we can."""
        try:
            return self.fixtures.get_plugin(instance_id=self.client_instance_id())
        except KeyError as err:
            raise RuntimeError(
                "Testkit provisioner cannot find its client plugin, and "
                "cannot process any client actions.  Was a client created?"
            ) from err
