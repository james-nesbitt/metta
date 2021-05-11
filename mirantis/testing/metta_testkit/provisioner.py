import logging
import os
import yaml
from typing import Any

from configerus.loaded import LOADED_KEY_ROOT
from configerus.contrib.jsonschema.validate import PLUGIN_ID_VALIDATE_JSONSCHEMA_SCHEMA_CONFIG_LABEL
from configerus.validator import ValidationError

from mirantis.testing.metta.plugin import Type
from mirantis.testing.metta.fixtures import UCCTFixturesPlugin
from mirantis.testing.metta.provisioner import ProvisionerBase

from .testkit import TestkitClient, TESTKITCLIENT_CLI_CONFIG_FILE_DEFAULT

logger = logging.getLogger('testkit.provisioner')

METTA_PLUGIN_ID_TESTKIT_PROVISIONER = 'metta_testkit'
TESTKIT_PROVISIONER_CONFIG_LABEL = 'testkit'
TESTKIT_PROVISIONER_CONFIG_BASE = LOADED_KEY_ROOT

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
        'mcr': { 'type': 'object' },
        'mke': { 'type': 'object' },
        'msr': { 'type': 'object' }
    },
    'required': []
}
""" Validation jsonschema for testkit configuration for the testkit yaml file """
METTA_TESTKIT_CONFIG_VALIDATE_TARGET = {
    PLUGIN_ID_VALIDATE_JSONSCHEMA_SCHEMA_CONFIG_LABEL: METTA_TESTKIT_CONFIG_VALIDATE_JSONSCHEMA
}
""" configerus jsonschema validation target for validation testkit config file structure """


METTA_TESTKIT_PROVISIONER_CONFIG_VALIDATE_JSONSCHEMA = {
    'type': 'object',
    'properties': {
        'opts': { 'type': 'object' },
        'config': METTA_TESTKIT_CONFIG_VALIDATE_JSONSCHEMA
    },
    'required': []
}
""" Validation jsonschema for provisioner configuration """
METTA_TESTKIT_PROVISIONER_CONFIG_VALIDATE_TARGET = {
    PLUGIN_ID_VALIDATE_JSONSCHEMA_SCHEMA_CONFIG_LABEL: METTA_TESTKIT_PROVISIONER_CONFIG_VALIDATE_JSONSCHEMA
}
""" configerus jsonschema validation target for the provisioner plugin """


class TestkitProvisionerPlugin(ProvisionerBase, UCCTFixturesPlugin):
    """ Testkit provisioner plugin

    Provisioner plugin that allows control of and interaction with a testkit
    cluster.

    ## Requirements

    1. this plugin uses subprocess to call a testkit binary, so you have to install
       testkit in the environment

    ## Usage

    @TODO

    """

    def __init__(self, environment, instance_id,
                 label: str = TESTKIT_PROVISIONER_CONFIG_LABEL, base: Any = TESTKIT_PROVISIONER_CONFIG_BASE):
        """

        Parameters:
        -----------

        environment (Environment) : metta environment object that this plugin is
            attached.
        instance_id (str) : label for this plugin instances.

        label (str) : config load label for plugin configuration.
        base (str) : config base for loaded config for plugin configuration.

        """
        super(ProvisionerBase, self).__init__(environment, instance_id)

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
        except KeyError as e:
            raise ValueError("Testkit plugin configuration did not have any config data: {}".format(e)) from e

        # instances = testkit_config.get([self.config_base, TESTKIT_CONFIG_KEY_INSTANCES])
        # """ what instances to create """

        self.config_file = testkit_config.get([self.config_base, TESTKIT_CONFIG_KEY_CONFIGFILE], default=TESTKIT_CONFIG_DEFAULT_CONFIGFILE)
        """ config_file value from plugin configuration """

        self.testkit = TestkitClient(config_file=self.config_file)
        """ testkit client object """

    def info(self, deep: bool = False):
        """ get info about a provisioner plugin """
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
        """ prepare any needed resources

        We don't create the testkit file here so that it is created as late as
        possible.  This allows more options for dynamic config sources in the
        testkit config.

        """
        pass


    def apply(self):
        """ create the testkit yaml file and run testkit to create a cluster """
        self._write_config_file()

        testkit_config = self.environment.config.load(self.config_label, force_reload=True)
        """ load the plugin configuration so we can retrieve options """
        opts = testkit_config.get([self.config_base, TESTKIT_CONFIG_KEY_CREATE_OPTIONS], default={})
        """ retrieve testkit client options from config """
        opt_list = []
        for key, value in opts.items():
            opt_list.append('--{key}={value}'.format(key=key, value=value))

        # run the testkit client command to provisioner the cluster
        self.testkit.create(opts=opt_list)


    def destroy(self):
        """ Destroy any created resources """
        # run the testkit client command to provisioner the cluster
        self.testkit.system_rm(self.system_name)
        self._rm_config_file()


    def _write_config_file(self):
        """ write the config file for testkit """
        try:
            """ load all of the testkit configuration, force a reload to get up to date contents """
            testkit_config = self.environment.config.load(
                self.config_label, force_reload=True)
            config = testkit_config.get(
                [self.config_base, TESTKIT_CONFIG_KEY_CONFIG], validator=METTA_TESTKIT_CONFIG_VALIDATE_TARGET)
            """ config source of launchpad yaml """
        except KeyError as e:
            raise ValueError(
                "Could not find launchpad configuration from config.")
        except ValidationError as e:
            raise ValueError(
                "Launchpad config failed validation: {}".format(e)) from e

        # write the configto our yaml file target (creating the path)
        os.makedirs(
            os.path.dirname(
                os.path.realpath(
                    self.config_file)),
            exist_ok=True)
        with open(os.path.realpath(self.config_file), 'w') as file:
            yaml.dump(config, file)

    def _rm_config_file(self):
        """ remove the written config file, so that no system record is in place """
        if os.path.isfile(self.config_file):
            os.remove(self.config_file)
