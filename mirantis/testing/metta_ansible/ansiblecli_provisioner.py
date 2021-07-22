"""

Ansible METTA provisioner plugin

This package is a WIP and currently doesn't really do anything.

"""

import os
import logging
from typing import Any, Dict

import toml
import yaml

from configerus.loaded import LOADED_KEY_ROOT

from mirantis.testing.metta.fixtures import Fixtures

from .ansiblecli_client import (
    METTA_ANSIBLE_ANSIBLECLI_CORECLIENT_PLUGIN_ID,
    METTA_ANSIBLE_ANSIBLECLI_PLAYBOOKCLIENT_PLUGIN_ID,
)

logger = logging.getLogger("metta.contrib.provisioner:ansible")

METTA_ANSIBLE_ANSIBLECLIPLAYBOOK_PROVISIONER_PLUGIN_ID = "metta_ansiblecliplaybook_provisioner"
""" Ansible provisioner plugin id """

ANSIBLE_PROVISIONER_CONFIG_LABEL = "ansible"
""" config label loading the ansible config """
ANSIBLE_PROVISIONER_CONFIG_PLAYBOOK_KEY = "playbook.contents"
""" config key for the ansible playbook content """
ANSIBLE_PROVISIONER_CONFIG_PLAYBOOK_PATH_KEY = "playbook.path"
""" config key for the ansible playbook path to write to."""
ANSIBLE_PROVISIONER_CONFIG_ANSIBLECFG_KEY = "ansiblecfg.contents"
""" config key for the ansible cfg contents which will be written to file """
ANSIBLE_PROVISIONER_CONFIG_ANSIBLECFG_PATH_KEY = "ansiblecfg.path"
""" config key for the ansible cfg file path to write to."""
ANSIBLE_PROVISIONER_CONFIG_INVENTORY_KEY = "inventory.contents"
""" config key for the ansible  inventory, which will be passed to ansible """
ANSIBLE_PROVISIONER_CONFIG_INVENTORY_PATH_KEY = "inventory.path"
""" config key for the ansible inventory file path to write to."""


# pylint: disable=too-many-instance-attributes
class AnsiblePlaybookProvisionerPlugin:
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
        self._environment = environment
        self._instance_id = instance_id

        logger.info("Preparing Ansible setting")

        self._config_label = label
        """ configerus load label that should contain all of the config """
        self._config_base = base
        """ configerus get key that should contain all tf config """

        self.fixtures: Fixtures = Fixtures()
        """Fixtures created by this plugin - typically various clients."""

        # In order to allow declarative interaction. Try to make an ansible client
        # for this plugin, but allow it to fail.
        try:
            self._update_config()
            self._make_clients()

        # no exception in init should block building the object
        # pylint: disable=broad-except
        except Exception:
            logger.debug("Inital ansible plugin build failed : %s", self._instance_id)

    # deep argument is an info() standard across plugins
    # pylint: disable=unused-argument
    def info(self, deep: bool = False):
        """get info about a provisioner plugin"""
        plugin_config = self._environment.config.load(self._config_label)
        """Loaded configerus config for the plugin. Ready for .get()."""

        return {
            "config": {
                "config_label": self._config_label,
                "config_base": self._config_base,
            },
            "ansible": {
                "ansiblecfg": plugin_config.get(
                    [self._config_base, ANSIBLE_PROVISIONER_CONFIG_ANSIBLECFG_KEY],
                    default="NONE",
                ),
                "inventory": plugin_config.get(
                    [self._config_base, ANSIBLE_PROVISIONER_CONFIG_INVENTORY_KEY],
                    default="MISSING",
                ),
                "playbook": plugin_config.get(
                    [self._config_base, ANSIBLE_PROVISIONER_CONFIG_PLAYBOOK_KEY],
                    default="MISSING",
                ),
            },
            "files": {
                "ansiblecfg": plugin_config.get(
                    [self._config_base, ANSIBLE_PROVISIONER_CONFIG_ANSIBLECFG_PATH_KEY],
                    default="NONE",
                ),
                "inventory": plugin_config.get(
                    [self._config_base, ANSIBLE_PROVISIONER_CONFIG_INVENTORY_PATH_KEY],
                    default="NONE",
                ),
                "playbook": plugin_config.get(
                    [self._config_base, ANSIBLE_PROVISIONER_CONFIG_PLAYBOOK_PATH_KEY],
                    default="NONE",
                ),
            },
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

        """
        self._update_config()
        self._make_clients()

        playbook_client = self.fixtures.get_plugin(
            plugin_id=METTA_ANSIBLE_ANSIBLECLI_PLAYBOOKCLIENT_PLUGIN_ID
        )

        plugin_config = self._environment.config.load(self._config_label)
        """Loaded configerus config for the plugin. Ready for .get()."""

        playbook_path: Dict[str, Any] = plugin_config.get(
            [self._config_base, ANSIBLE_PROVISIONER_CONFIG_PLAYBOOK_PATH_KEY]
        )

        playbook_client.run_file(playbook_path)

    def destroy(self):
        """remove all resources created for the cluster

        Run an aansible palybook to remove any implemented changes

        @NOTE his plugin ist still very much a stub, and implements no real functionality.

        """
        self._rm_ansible_files()

    def _make_clients(self):
        """Create and assign an ansible client to this plugin."""
        plugin_config = self._environment.config.load(self._config_label, force_reload=True)
        """Loaded configerus config for the plugin. Ready for .get()."""

        ansiblecfg_path: str = plugin_config.get(
            [self._config_base, ANSIBLE_PROVISIONER_CONFIG_ANSIBLECFG_PATH_KEY],
            default="",
        )
        inventory_path: str = plugin_config.get(
            [self._config_base, ANSIBLE_PROVISIONER_CONFIG_INVENTORY_PATH_KEY]
        )

        inventory_contents: str = plugin_config.get(
            [self._config_base, ANSIBLE_PROVISIONER_CONFIG_INVENTORY_KEY]
        )
        playbook_contents: str = plugin_config.get(
            [self._config_base, ANSIBLE_PROVISIONER_CONFIG_PLAYBOOK_KEY]
        )

        # Don't create the object unless we think we hae enough config for it
        if not (inventory_path and inventory_contents and playbook_contents):
            raise RuntimeError("No inventory provided so we are not creating an ansible client.")

        instance_id = f"{self._instance_id}-{METTA_ANSIBLE_ANSIBLECLI_CORECLIENT_PLUGIN_ID}"
        fixture = self._environment.add_fixture(
            plugin_id=METTA_ANSIBLE_ANSIBLECLI_CORECLIENT_PLUGIN_ID,
            instance_id=instance_id,
            priority=70,
            arguments={
                "ansiblecfg_path": ansiblecfg_path,
                "inventory_path": inventory_path,
            },
            replace_existing=True,
        )
        self.fixtures.add(fixture, replace_existing=True)

        instance_id = f"{self._instance_id}-{METTA_ANSIBLE_ANSIBLECLI_PLAYBOOKCLIENT_PLUGIN_ID}"
        fixture = self._environment.add_fixture(
            plugin_id=METTA_ANSIBLE_ANSIBLECLI_PLAYBOOKCLIENT_PLUGIN_ID,
            instance_id=instance_id,
            priority=70,
            arguments={
                "ansiblecfg_path": ansiblecfg_path,
                "inventory_path": inventory_path,
            },
            replace_existing=True,
        )
        self.fixtures.add(fixture, replace_existing=True)

    def _update_config(self):
        """Update config and write the cfg and inventory files."""
        # refresh any loaded config
        plugin_config = self._environment.config.load(self._config_label, force_reload=True)
        """Loaded configerus config for the plugin. Ready for .get()."""

        # first the ansible cfg file
        ansiblecfg_contents: Dict[str, Any] = plugin_config.get(
            [self._config_base, ANSIBLE_PROVISIONER_CONFIG_ANSIBLECFG_KEY], default={}
        )
        ansiblecfg_path: str = plugin_config.get(
            [self._config_base, ANSIBLE_PROVISIONER_CONFIG_ANSIBLECFG_PATH_KEY],
            default="",
        )
        if ansiblecfg_contents:
            # ansible doesn't like how toml keeps some quotes - so we have to do this ourselves.
            ansiblecfg_contents = toml.dumps(ansiblecfg_contents)
            ansiblecfg_contents = ansiblecfg_contents.replace('"', "")
            os.makedirs(os.path.dirname(os.path.realpath(ansiblecfg_path)), exist_ok=True)
            with open(ansiblecfg_path, "w") as ansiblecfg_fileobject:
                ansiblecfg_fileobject.write(ansiblecfg_contents)

        else:
            if ansiblecfg_path and os.path.exists(ansiblecfg_path):
                os.remove(ansiblecfg_path)

        # second the inventory file
        inventory_contents: str = plugin_config.get(
            [self._config_base, ANSIBLE_PROVISIONER_CONFIG_INVENTORY_KEY], default={}
        )
        inventory_path: str = plugin_config.get(
            [self._config_base, ANSIBLE_PROVISIONER_CONFIG_INVENTORY_PATH_KEY],
            default="",
        )
        if inventory_contents:
            os.makedirs(os.path.dirname(os.path.realpath(inventory_path)), exist_ok=True)
            with open(inventory_path, "w") as inventory_fileobject:
                inventory_fileobject.write(inventory_contents)
        else:
            if inventory_path and os.path.exists(inventory_path):
                os.remove(inventory_path)

        # the playbook file
        playbook_contents: str = plugin_config.get(
            [self._config_base, ANSIBLE_PROVISIONER_CONFIG_PLAYBOOK_KEY], default={}
        )
        playbook_path: str = plugin_config.get(
            [self._config_base, ANSIBLE_PROVISIONER_CONFIG_PLAYBOOK_PATH_KEY],
            default="",
        )
        if playbook_contents:
            os.makedirs(os.path.dirname(os.path.realpath(playbook_path)), exist_ok=True)
            with open(playbook_path, "w") as playbook_fileobject:
                yaml.safe_dump(playbook_contents, playbook_fileobject)
        else:
            if playbook_path and os.path.exists(playbook_path):
                os.remove(playbook_path)

    def _rm_ansible_files(self):
        """Update config and write the cfg and inventory files."""

        logger.info("Ansible provisioner removing created files.")

        plugin_config = self._environment.config.load(self._config_label)
        """Loaded configerus config for the plugin. Ready for .get()."""

        # first the ansible cfg file
        ansiblecfg_path: str = plugin_config.get(
            [self._config_base, ANSIBLE_PROVISIONER_CONFIG_ANSIBLECFG_PATH_KEY],
            default="",
        )
        if ansiblecfg_path and os.path.exists(ansiblecfg_path):
            os.remove(ansiblecfg_path)

        # second the inventory file
        inventory_path: str = plugin_config.get(
            [self._config_base, ANSIBLE_PROVISIONER_CONFIG_INVENTORY_PATH_KEY],
            default="",
        )
        if inventory_path and os.path.exists(inventory_path):
            os.remove(inventory_path)

        # the playbook file
        playbook_path: str = plugin_config.get(
            [self._config_base, ANSIBLE_PROVISIONER_CONFIG_PLAYBOOK_PATH_KEY],
            default="",
        )
        if playbook_path and os.path.exists(playbook_path):
            os.remove(playbook_path)
