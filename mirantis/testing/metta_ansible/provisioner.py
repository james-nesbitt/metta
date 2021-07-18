"""

Ansible METTA provisioner plugin

This package is a WIP and currently doesn't really do anything.

"""

import os
import logging
from typing import Any, Dict

import toml

from configerus.loaded import LOADED_KEY_ROOT

from mirantis.testing.metta.provisioner import ProvisionerBase
from mirantis.testing.metta.healthcheck import Health

from .ansible_play import AnsiblePlay
from .ansible_callback import ResultStatus

logger = logging.getLogger("metta.contrib.provisioner:ansible")

METTA_ANSIBLE_PROVISIONER_PLUGIN_ID = "metta_ansible_provisioner"
""" Ansible provisioner plugin id """

ANSIBLE_PROVISIONER_CONFIG_LABEL = "ansible"
""" config label loading the ansible config """
ANSIBLE_PROVISIONER_CONFIG_PLAYBOOKS_KEY = "playbooks"
""" config key for the ansible playbooks path """
ANSIBLE_PROVISIONER_CONFIG_ANSIBLECFG_KEY = "ansiblecfg.contents"
""" config key for the ansible cfg contents which will be written to file """
ANSIBLE_PROVISIONER_CONFIG_ANSIBLECFG_PATH_KEY = "ansiblecfg.path"
""" config key for the ansible cfg file path to write to."""
ANSIBLE_PROVISIONER_CONFIG_INVENTORY_KEY = "inventory.contents"
""" config key for the ansible  inventory, which will be passed to ansible """
ANSIBLE_PROVISIONER_CONFIG_INVENTORY_PATH_KEY = "inventory.path"
""" config key for the ansible inventory file path to write to."""


# pylint: disable=too-many-instance-attributes
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
        self._environment = environment
        self._instance_id = instance_id

        logger.info("Preparing Ansible setting")

        self._config_label = label
        """ configerus load label that should contain all of the config """
        self._config_base = base
        """ configerus get key that should contain all tf config """

        self._ansiblecfg_contents: Dict[str, Any] = {}
        """Contents for the ansible cfg file."""
        self._ansiblecfg_path: str = ""
        """Path for the ansible cfg file."""
        self._inventory_contents: str = ""
        """Contents for the ansible inventory file."""
        self._inventory_path: str = ""
        """Path for the ansible inventory file."""

        self._ansible: AnsiblePlay = None
        """Plugin instance of the ansible plugin."""

        # In order to allow declarative interaction. Try to make an ansible client
        # for this plugin, but allow it to fail.
        # try:
        self._update_config()
        self._write_ansible_files()
        self._make_ansible_client()
        # except Exception:
        #    logger.debug('Inital ansible plugin build failed : %s', self._instance_id)

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
                    default={},
                ),
                "inventory": plugin_config.get(
                    [self._config_base, ANSIBLE_PROVISIONER_CONFIG_INVENTORY_KEY],
                    default={},
                ),
                "playbooks": plugin_config.get(
                    [self._config_base, ANSIBLE_PROVISIONER_CONFIG_PLAYBOOKS_KEY],
                    default={},
                ),
            },
            "files": {
                "ansiblecfg": plugin_config.get(
                    [self._config_base, ANSIBLE_PROVISIONER_CONFIG_ANSIBLECFG_PATH_KEY],
                    default="",
                ),
                "inventory": plugin_config.get(
                    [self._config_base, ANSIBLE_PROVISIONER_CONFIG_INVENTORY_PATH_KEY],
                    default="",
                ),
            },
        }

    def health(self) -> Health:
        """Return health status of the cluster."""
        ansible_health = Health(source=self._instance_id)

        if self._ansible:
            for test_health_function in [
                self._health_all_ping,
            ]:
                test_health = test_health_function()
                ansible_health.merge(test_health)

        return ansible_health

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
        self._update_config()
        self._write_ansible_files()

    def apply(self):
        """bring a cluster to the configured state

        Run an ansible playbook to execute functionality on a running cluster.

        """
        self._ansible.play({})

    def destroy(self):
        """remove all resources created for the cluster

        Run an aansible palybook to remove any implemented changes

        @NOTE his plugin ist still very much a stub, and implements no real functionality.

        """

    def _make_ansible_client(self):
        """Create and assign an ansible client to this plugin."""
        self._ansible = AnsiblePlay(
            ansiblecfg_path=self._ansiblecfg_path,
            inventory_path=self._inventory_path,
        )

    def _update_config(self):
        """Update config and write the cfg and inventory files."""
        # refresh any loaded config
        plugin_config = self._environment.config.load(self._config_label)
        """Loaded configerus config for the plugin. Ready for .get()."""

        # first the ansible cfg file
        self._ansiblecfg_contents: Dict[str, Any] = plugin_config.get(
            [self._config_base, ANSIBLE_PROVISIONER_CONFIG_ANSIBLECFG_KEY], default={}
        )
        self._ansiblecfg_path: str = plugin_config.get(
            [self._config_base, ANSIBLE_PROVISIONER_CONFIG_ANSIBLECFG_PATH_KEY],
            default="",
        )

        # second the inventory file
        self._inventory_contents: str = plugin_config.get(
            [self._config_base, ANSIBLE_PROVISIONER_CONFIG_INVENTORY_KEY], default={}
        )
        self._inventory_path: str = plugin_config.get(
            [self._config_base, ANSIBLE_PROVISIONER_CONFIG_INVENTORY_PATH_KEY],
            default="",
        )

    def _write_ansible_files(self):
        """Update config and write the cfg and inventory files."""
        # first the ansible cfg file
        if self._ansiblecfg_contents:
            os.makedirs(os.path.dirname(os.path.realpath(self._ansiblecfg_path)), exist_ok=True)
            with open(self._ansiblecfg_path, "w") as ansiblecfg_fileobject:
                toml.dump(self._ansiblecfg_contents, ansiblecfg_fileobject)
        # second the inventory file
        if self._inventory_contents:
            os.makedirs(os.path.dirname(os.path.realpath(self._inventory_path)), exist_ok=True)
            with open(self._inventory_path, "w") as inventory_fileobject:
                inventory_fileobject.write(self._inventory_contents)

    def _health_all_ping(self) -> Health:
        """Health check that tries to ping all of the hosts."""
        ping_health = Health(source=self._instance_id)

        for result in self._ansible.ping():
            if result.status == ResultStatus.OK:
                ping_health.healthy(f"Ansible: {result.host} ping response ok.")
            elif result.status == ResultStatus.UNREACHABLE:
                ping_health.warning(f"Ansible: {result.host} unreachable during ping.")
            elif ping_health.status == ResultStatus.FAILED:
                ping_health.error(f"Ansible: {result.host} ping failed.")
            else:
                ping_health.warning(
                    f"Ansible: {result.host} status not understood: {ping_health.status}."
                )

        return ping_health
