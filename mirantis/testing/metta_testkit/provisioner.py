"""

Metta provisioner plugin for testkit.

"""
import logging
import os
from typing import Any, Dict

import yaml

from configerus.loaded import LOADED_KEY_ROOT
from configerus.contrib.jsonschema.validate import PLUGIN_ID_VALIDATE_JSONSCHEMA_SCHEMA_CONFIG_LABEL
from configerus.validator import ValidationError

from mirantis.testing.metta.fixtures import Fixtures
from mirantis.testing.metta.provisioner import ProvisionerBase

from .testkit import TestkitClient, TESTKITCLIENT_CLI_CONFIG_FILE_DEFAULT

logger = logging.getLogger('testkit.provisioner')

METTA_PLUGIN_ID_TESTKIT_PROVISIONER = 'metta_testkit'
""" Metta plugin id for testkit provisioner plugins """

TESTKIT_PROVISIONER_CONFIG_LABEL = 'testkit'
TESTKIT_PROVISIONER_CONFIG_BASE = LOADED_KEY_ROOT
""" configerus config label/base-key for loading testkit provisioner config """

TESTKIT_CONFIG_KEY_SYSTEMNAME = 'system_name'
""" config key to find the system name """
TESTKIT_CONFIG_KEY_CREATE_OPTIONS = 'options.create'
""" config key to find where the testkit create options """
TESTKIT_CONFIG_KEY_CONFIG = 'config'
""" config key to find where to put the testkit config file data/contents """
TESTKIT_CONFIG_KEY_INSTANCES = 'instances'
""" config key to find what instances to spec out (build) """
TESTKIT_CONFIG_KEY_CONFIGFILE = 'config_file'
""" config key to find where to put the testkit config file """
TESTKIT_CONFIG_DEFAULT_CONFIGFILE = TESTKITCLIENT_CLI_CONFIG_FILE_DEFAULT
""" default value for where to put the testkit config file """

METTA_TESTKIT_CONFIG_VALIDATE_JSONSCHEMA = {
    'type': 'object',
    'properties': {
        'mcr': {'type': 'object'},
        'mke': {'type': 'object'},
        'msr': {'type': 'object'}
    },
    'required': []
}
""" Validation jsonschema for testkit configuration for testkit yaml files """
METTA_TESTKIT_CONFIG_VALIDATE_TARGET = {
    PLUGIN_ID_VALIDATE_JSONSCHEMA_SCHEMA_CONFIG_LABEL: METTA_TESTKIT_CONFIG_VALIDATE_JSONSCHEMA
}
""" configerus jsonschema validation target for testkit config file """

METTA_TESTKIT_PROVISIONER_CONFIG_VALIDATE_JSONSCHEMA = {
    'type': 'object',
    'properties': {
        'opts': {'type': 'object'},
        'config': METTA_TESTKIT_CONFIG_VALIDATE_JSONSCHEMA
    },
    'required': []
}
""" Validation jsonschema for provisioner configuration """
METTA_TESTKIT_PROVISIONER_CONFIG_VALIDATE_TARGET = {
    PLUGIN_ID_VALIDATE_JSONSCHEMA_SCHEMA_CONFIG_LABEL: METTA_TESTKIT_PROVISIONER_CONFIG_VALIDATE_JSONSCHEMA
}
""" configerus jsonschema validation target for the provisioner plugin """


# pylint: disable=too-many-instance-attributes
class TestkitProvisionerPlugin(ProvisionerBase):
    """Testkit provisioner plugin.

    Provisioner plugin that allows control of and interaction with a testkit
    cluster.

    ## Requirements

    1. this plugin uses subprocess to call a testkit binary, so you have to
       install testkit in the environment

    ## Usage

    @TODO

    """

    def __init__(self, environment, instance_id, label: str = TESTKIT_PROVISIONER_CONFIG_LABEL,
                 base: Any = TESTKIT_PROVISIONER_CONFIG_BASE):
        """Initialize Testkit provisioner.

        Parameters:
        -----------
        environment (Environment) : metta environment object that this plugin
            is attached.
        instance_id (str) : label for this plugin instances.

        label (str) : config load label for plugin configuration.
        base (str) : config base for loaded config for plugin configuration.

        """
        self.environment = environment
        """ Environemnt in which this plugin exists """
        self.instance_id = instance_id
        """ Unique id for this plugin instance """

        self.fixtures = Fixtures()
        """ Keep a collection of all fixtures created by this plugin """

        logger.info("Preparing Testkit setting")

        self.config_label = label
        """ configerus load label that should contain all of the config """
        self.config_base = base

        testkit_config = self.environment.config.load(self.config_label, force_reload=True)
        """ load the plugin configuration so we can retrieve options """

        self.system_name = testkit_config.get([self.config_base, TESTKIT_CONFIG_KEY_SYSTEMNAME])
        """ hat will testkit call the system """

        try:
            testkit_config = self.environment.config.load(self.config_label)
            """ loaded plugin configuration label """
        except KeyError as err:
            raise ValueError("Testkit plugin configuration did not have any config") from err

        # instances = testkit_config.get([self.config_base, TESTKIT_CONFIG_KEY_INSTANCES])
        # """ what instances to create """

        self.config_file = testkit_config.get([self.config_base, TESTKIT_CONFIG_KEY_CONFIGFILE],
                                              default=TESTKIT_CONFIG_DEFAULT_CONFIGFILE)
        """ config_file value from plugin configuration """

        self.testkit = TestkitClient(config_file=self.config_file)
        """ testkit client object """

    # the deep argument is a standard for the info hook
    # pylint: disable=unused-argument
    def info(self, deep: bool = False) -> Dict[str, Any]:
        """Get info about a provisioner plugin."""
        plugin = self
        client = self.testkit
        testkit_config = self.environment.config.load(self.config_label)

        info = {
            'plugin': {
                'config_label': plugin.config_label,
                'config_base': plugin.config_base,
                'system_name': self.system_name
            },
            'client': {
                'config_file': client.config_file,
                'working_dir': client.working_dir,
                'bin': client.bin,
                'version': client.version()
            },
            # 'instances': testkit_config.get([self.config_base, TESTKIT_CONFIG_KEY_INSTANCES]),
            'config': testkit_config.get([self.config_base, TESTKIT_CONFIG_KEY_CONFIG])
        }

        return info

    def prepare(self):
        """Prepare any needed resources.

        We don't create the testkit file here so that it is created as late as
        possible.  This allows more options for dynamic config sources in the
        testkit config.

        """

    def apply(self):
        """Create the testkit yaml file and run testkit to create a cluster."""
        self._write_config_file()

        testkit_config = self.environment.config.load(self.config_label, force_reload=True)
        """ load the plugin configuration so we can retrieve options """
        opts = testkit_config.get([self.config_base, TESTKIT_CONFIG_KEY_CREATE_OPTIONS], default={})
        """ retrieve testkit client options from config """
        opt_list = []
        for key, value in opts.items():
            opt_list.append(f'--{key}={value}')

        # run the testkit client command to provisioner the cluster
        self.testkit.create(opts=opt_list)

    def destroy(self):
        """Destroy any created resources."""
        # run the testkit client command to provisioner the cluster
        self.testkit.system_rm(self.system_name)
        self._rm_config_file()

    def _write_config_file(self):
        """Write the config file for testkit."""
        try:
            # load all of the testkit configuration, force a reload to get up to date contents
            testkit_config = self.environment.config.load(self.config_label, force_reload=True)
            config = testkit_config.get([self.config_base, TESTKIT_CONFIG_KEY_CONFIG],
                                        validator=METTA_TESTKIT_CONFIG_VALIDATE_TARGET)
            """ config source of launchpad yaml """
        except KeyError as err:
            raise ValueError("Could not find launchpad configuration from config.") from err
        except ValidationError as err:
            raise ValueError("Launchpad config failed validation") from err

        # write the configto our yaml file target (creating the path)
        os.makedirs(os.path.dirname(os.path.realpath(self.config_file)), exist_ok=True)
        with open(os.path.realpath(self.config_file), 'w') as file:
            yaml.dump(config, file)

    def _rm_config_file(self):
        """Remove the written config file."""
        if os.path.isfile(self.config_file):
            os.remove(self.config_file)
