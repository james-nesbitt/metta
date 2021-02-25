"""

Ansible METTA provisioner plugin

"""

import logging
import json
import os
import subprocess
from typing import Dict, List, Any

from configerus.loaded import LOADED_KEY_ROOT
from mirantis.testing.metta.plugin import METTAPlugin, Type
from mirantis.testing.metta.fixtures import Fixtures, UCCTFixturesPlugin, METTA_FIXTURES_CONFIG_FIXTURES_LABEL
from mirantis.testing.metta.provisioner import ProvisionerBase
from mirantis.testing.metta.output import OutputBase
from mirantis.testing.metta_common import METTA_PLUGIN_ID_OUTPUT_DICT, METTA_PLUGIN_ID_OUTPUT_TEXT

logger = logging.getLogger('metta.contrib.provisioner:ansible')

ANSIBLE_PROVISIONER_CONFIG_LABEL = 'ansible'
""" config label loading the ansible config """
ANSIBLE_PROVISIONER_CONFIG_PLAN_PATH_KEY = 'plan.path'
""" config key for the ansible plan path """
ANSIBLE_PROVISIONER_CONFIG_STATE_PATH_KEY = 'state.path'
""" config key for the ansible state path """
ANSIBLE_PROVISIONER_CONFIG_VARS_KEY = 'vars'
""" config key for the ansible vars Dict, which will be written to a file """
ANSIBLE_PROVISIONER_CONFIG_VARS_PATH_KEY = 'vars_path'
""" config key for the ansible vars file path, where the plugin will write to """
ANSIBLE_PROVISIONER_DEFAULT_VARS_FILE = 'metta_ansible.tfvars.json'
""" Default vars file if none was specified """
ANSIBLE_PROVISIONER_DEFAULT_STATE_SUBPATH = 'metta-state'
""" Default vars file if none was specified """


class AnsibleProvisionerPlugin(ProvisionerBase, UCCTFixturesPlugin):
    """ Ansible provisioner plugin

    Provisioner plugin that allows control of and interaction with a ansible
    cluster.

    ## Requirements

    1. this plugin uses subprocess to call a ansible binary, so you have to install
       ansible in the environment

    ## Usage

    ### Plan

    The plan must exists somewhere on disk, and be accessible.

    You must specify the path and related configuration in config, which are read
    in the .prepare() execution.

    ### Vars/State

    This plugin reads TF vars from config and writes them to a vars file.  We
    could run without relying on vars file, but having a vars file allows cli
    interaction with the cluster if this plugin messes up.

    You can override where Ansible vars/state files are written to allow sharing
    of a plan across test suites.

    """

    def __init__(self, environment, instance_id,
                 label: str = ANSIBLE_PROVISIONER_CONFIG_LABEL, base: Any = LOADED_KEY_ROOT):
        """ Run the super constructor but also set class properties

        Interpret provided config and configure the object with all of the needed
        pieces for executing ansible commands

        """
        super(ProvisionerBase, self).__init__(environment, instance_id)

        logger.info("Preparing Ansible setting")

        self.config_label = label
        """ configerus load label that should contain all of the config """
        self.config_base = base
        """ configerus get key that should contain all tf config """

        fixtures = self.environment.add_fixtures_from_config(
            label=self.config_label,
            base=[self.config_base, METTA_FIXTURES_CONFIG_FIXTURES_LABEL])
        """ All fixtures added to this provisioner plugin. """
        UCCTFixturesPlugin.__init__(self, fixtures)

        self.ansible_config = self.environment.config.load(
            self.config_label)
        """ get a configerus LoadedConfig for the ansible label """

    def info(self):
        """ get info about a provisioner plugin """
        return {
            'plugin': {
                'config_label': self.config_label,
                'config_base': self.config_base
            }
        }

    def prepare(self, label: str = '', base: str = ''):
        """ Prepare the provisioner to apply resources

        Initial Provisioner plugin is expected to be of very low cost until
        prepare() is executed.  At this point the plugin should load any config
        and perform any validations needed.
        The plugin should not create any resources but it is understood that
        there may be a cost of preparation.

        Provisioners are expected to load a lot of config to self-program.
        Because of this, they allow passing of a configerus label for .load()
        and a base for .get() in case there is an alterante config source
        desired.

        """
        pass

    def apply(self):
        """ bring a cluster to the configured state """
        pass

    def destroy(self):
        """ remove all resources created for the cluster """
        pass
