"""

Ansible METTA provisioner plugin

This package is a WIP and currently doesn't really do anything.

"""

import logging
from typing import Any

from configerus.loaded import LOADED_KEY_ROOT

from mirantis.testing.metta.provisioner import ProvisionerBase

logger = logging.getLogger("metta.contrib.provisioner:ansible")

METTA_ANSIBLE_PROVISIONER_PLUGIN_ID = "metta_ansible_provisioner"
""" Ansible provisioner plugin id """

ANSIBLE_PROVISIONER_CONFIG_LABEL = "ansible"
""" config label loading the ansible config """
ANSIBLE_PROVISIONER_CONFIG_PLAN_PATH_KEY = "plan.path"
""" config key for the ansible plan path """
ANSIBLE_PROVISIONER_CONFIG_STATE_PATH_KEY = "state.path"
""" config key for the ansible state path """
ANSIBLE_PROVISIONER_CONFIG_VARS_KEY = "vars"
""" config key for the ansible vars Dict, which will be written to a file """
ANSIBLE_PROVISIONER_CONFIG_VARS_PATH_KEY = "vars_path"
""" config key for the ansible vars file path, where the plugin will write to """
ANSIBLE_PROVISIONER_DEFAULT_VARS_FILE = "metta_ansible.tfvars.json"
""" Default vars file if none was specified """
ANSIBLE_PROVISIONER_DEFAULT_STATE_SUBPATH = "metta-state"
""" Default vars file if none was specified """


class AnsibleProvisionerPlugin(ProvisionerBase):
    """Ansible provisioner plugin

    Provisioner plugin that allows control of and interaction with a ansible
    cluster.

    ## Requirements

    1. this plugin uses subprocess to call a ansible binary, so you have to install
       ansible in the environment

    ## Usage

    @NOTE his plugin ist still very much a stub, and implements no real functionality.

    """

    def __init__(
        self,
        environment,
        instance_id,
        label: str = ANSIBLE_PROVISIONER_CONFIG_LABEL,
        base: Any = LOADED_KEY_ROOT,
    ):
        """Run the super constructor but also set class properties

        Interpret provided config and configure the object with all of the needed
        pieces for executing ansible commands

        """
        super().__init__(environment, instance_id)

        logger.info("Preparing Ansible setting")

        self.config_label = label
        """ configerus load label that should contain all of the config """
        self.config_base = base
        """ configerus get key that should contain all tf config """

    # deep argument is an info() standard across plugins
    # pylint: disable=unused-argument
    def info(self, deep: bool = False):
        """get info about a provisioner plugin"""
        return {
            "plugin": {
                "config_label": self.config_label,
                "config_base": self.config_base,
            }
        }

    def prepare(self):
        """Prepare the provisioner to apply resources

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

    def apply(self):
        """bring a cluster to the configured state

        Run an ansible playbook to execute functionality on a running cluster.

        @NOTE his plugin ist still very much a stub, and implements no real functionality.

        """

    def destroy(self):
        """remove all resources created for the cluster

        Run an aansible palybook to remove any implemented changes

        @NOTE his plugin ist still very much a stub, and implements no real functionality.

        """
