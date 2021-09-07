"""

Metta workload plugins that rely on ansiblecli clients.

Classes:
--------

AnsibleCliCoreWorkloadPlugin: Workload plugin for running ansible cli

AnsibleCliPlaybookWorkloadPlugin: Workload plugin for running ansible-playbook cli

"""
from typing import Dict, List, Any
import os

import yaml

from configerus.loaded import LOADED_KEY_ROOT

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.fixture import Fixtures

from .ansiblecli_client import (
    AnsibleClientPlugin,
    AnsiblePlaybookClientPlugin,
    METTA_ANSIBLE_ANSIBLECLI_CORECLIENT_PLUGIN_ID,
    METTA_ANSIBLE_ANSIBLECLI_PLAYBOOKCLIENT_PLUGIN_ID,
)

METTA_ANSIBLE_ANSIBLECLI_COREWORKLOAD_PLUGIN_ID = "metta_ansible_clicore_ansible_workload"
""" Ansible workload plugin id """

METTA_ANSIBLE_ANSIBLECLI_PLAYBOOKWORKLOAD_PLUGIN_ID = (
    "metta_ansible_clicore_ansibleplaybook_workload"
)
""" Ansible-Playbook workload plugin id """

ANSIBLE_WORKLOAD_CONFIG_LABEL = "ansible"
""" default config label loading ansible config """

ANSIBLE_WORKLOAD_CONFIG_ARGS_KEY = "args"
"""Configures key for loading args."""
ANSIBLE_WORKLOAD_CONFIG_ENVS_KEY = "envs"
"""Configerus key for loading env variables to be used for clients."""
ANSIBLE_WORKLOAD_CONFIG_PLAYBOOK_KEY = "playbook.contents"
""" config key for the ansible playbook content """
ANSIBLE_WORKLOAD_CONFIG_PLAYBOOK_PATH_KEY = "playbook.path"
""" config key for the ansible playbook path to write to."""
ANSIBLE_WORKLOAD_CONFIG_PLAYBOOK_VARS_KEY = "vars.values"
""" config key for the ansible playbook vars."""
ANSIBLE_WORKLOAD_CONFIG_PLAYBOOK_VARS_PATH_KEY = "vars.path"
""" config key for the ansible playbook vars path to write to."""
ANSIBLE_WORKLOAD_CONFIG_ANSIBLECFG_KEY = "ansiblecfg.contents"
""" config key for the ansible cfg contents which will be written to file """
ANSIBLE_WORKLOAD_CONFIG_ANSIBLECFG_PATH_KEY = "ansiblecfg.path"
""" config key for the ansible cfg file path to write to."""
ANSIBLE_WORKLOAD_CONFIG_INVENTORY_KEY = "inventory.contents"
""" config key for the ansible  inventory, which will be passed to ansible """
ANSIBLE_WORKLOAD_CONFIG_INVENTORY_PATH_KEY = "inventory.path"
""" config key for the ansible inventory file path to write to."""


class AnsibleCliCoreWorkloadPlugin:
    """An ansiblecli workload that uses an AnsibleClientPlugin client."""

    def __init__(
        self,
        environment: Environment,
        instance_id: str,
        label: str = ANSIBLE_WORKLOAD_CONFIG_LABEL,
        base: Any = LOADED_KEY_ROOT,
    ):
        """Keep metta info and plugin config info."""
        self._environment: Environment = environment
        self._instance_id: str = instance_id

        self._config_label: str = label
        """ configerus load label that should contain all of the config """
        self._config_base: str = base
        """ configerus get key that should contain all plugin config """

        self._ansible_client: AnsibleClientPlugin = None
        """AnsibleClientPlugin which this plugin will use to interact with ansible."""

    def info(self, deep: bool = False) -> Dict[str, Any]:
        """Get info about a provisioner plugin."""
        return {
            "config": {
                "label": self._config_label,
                "base": self._config_base,
            },
            "client-plugin": self._ansible_client.info(deep=deep)
            if self._ansible_client
            else "MISSING",
        }

    def prepare(self, fixtures: Fixtures = None):
        """Find the dependent fixtures."""
        if fixtures is None:
            fixtures = self._environment.fixtures()

        self._ansible_client = fixtures.get_plugin(
            plugin_id=METTA_ANSIBLE_ANSIBLECLI_CORECLIENT_PLUGIN_ID
        )

    def apply(self):
        """Apply the workload to the environment."""
        # Loaded configerus config for the plugin. Ready for .get().
        plugin_config = self._environment.config().load(self._config_label)

        args: List[str] = plugin_config.get([self._config_base, ANSIBLE_WORKLOAD_CONFIG_ARGS_KEY])
        envs: Dict[str, str] = plugin_config.get(
            [self._config_base, ANSIBLE_WORKLOAD_CONFIG_ENVS_KEY], default={}
        )

        return self._ansible_client.run(args=args, envs=envs)


class AnsibleCliPlaybookWorkloadPlugin:
    """An ansiblecli workload that uses an AnsiblePlaybookClientPlugin client."""

    def __init__(
        self,
        environment: Environment,
        instance_id: str,
        label: str = ANSIBLE_WORKLOAD_CONFIG_LABEL,
        base: Any = LOADED_KEY_ROOT,
    ):
        """Keep metta info and plugin config info."""
        self._environment: Environment = environment
        self._instance_id: str = instance_id

        self._config_label: str = label
        """ configerus load label that should contain all of the config """
        self._config_base: str = base
        """ configerus get key that should contain all plugin config """

        self._ansibleplaybook_client: AnsiblePlaybookClientPlugin = None
        """AnsiblePlaybookClientPlugin which this plugin will use to interact with ansible."""

    def info(self, deep: bool = False):
        """Get info about a provisioner plugin."""
        # Loaded configerus config for the plugin. Ready for .get().
        plugin_config = self._environment.config().load(self._config_label)

        return {
            "config": {
                "label": self._config_label,
                "base": self._config_base,
            },
            "plugin": {
                "playbook_contents": plugin_config.get(
                    [self._config_base, ANSIBLE_WORKLOAD_CONFIG_PLAYBOOK_KEY], default={}
                ),
                "playbook_path": plugin_config.get(
                    [self._config_base, ANSIBLE_WORKLOAD_CONFIG_PLAYBOOK_PATH_KEY],
                    default="",
                ),
                "envs": plugin_config.get(
                    [self._config_base, ANSIBLE_WORKLOAD_CONFIG_ENVS_KEY], default={}
                ),
                "vars_values": plugin_config.get(
                    [self._config_base, ANSIBLE_WORKLOAD_CONFIG_PLAYBOOK_VARS_KEY], default={}
                ),
                "vars_path": plugin_config.get(
                    [self._config_base, ANSIBLE_WORKLOAD_CONFIG_PLAYBOOK_VARS_PATH_KEY],
                    default="",
                ),
            },
            "client-plugin": self._ansibleplaybook_client.info(deep=deep)
            if self._ansibleplaybook_client
            else "MISSING",
        }

    def prepare(self, fixtures: Fixtures = None):
        """Find the dependent fixtures."""
        if fixtures is None:
            fixtures = self._environment.fixtures()

        self._ansibleplaybook_client = fixtures.get_plugin(
            plugin_id=METTA_ANSIBLE_ANSIBLECLI_PLAYBOOKCLIENT_PLUGIN_ID
        )

        # Loaded configerus config for the plugin. Ready for .get().
        plugin_config = self._environment.config().load(self._config_label)

        playbook_contents: str = plugin_config.get(
            [self._config_base, ANSIBLE_WORKLOAD_CONFIG_PLAYBOOK_KEY], default={}
        )
        playbook_path: str = plugin_config.get(
            [self._config_base, ANSIBLE_WORKLOAD_CONFIG_PLAYBOOK_PATH_KEY],
            default="",
        )
        vars_values: str = plugin_config.get(
            [self._config_base, ANSIBLE_WORKLOAD_CONFIG_PLAYBOOK_VARS_KEY], default={}
        )
        vars_path: str = plugin_config.get(
            [self._config_base, ANSIBLE_WORKLOAD_CONFIG_PLAYBOOK_VARS_PATH_KEY],
            default="",
        )

        if playbook_contents:
            os.makedirs(os.path.dirname(os.path.realpath(playbook_path)), exist_ok=True)
            with open(playbook_path, "w", encoding="utf8") as playbook_fileobject:
                yaml.safe_dump(playbook_contents, playbook_fileobject)
        else:
            if playbook_path and os.path.exists(playbook_path):
                os.remove(playbook_path)
        if vars_values:
            os.makedirs(os.path.dirname(os.path.realpath(vars_path)), exist_ok=True)
            with open(vars_path, "w", encoding="utf8") as vars_fileobject:
                yaml.safe_dump(vars_values, vars_fileobject)
        else:
            if vars_path and os.path.exists(vars_path):
                os.remove(vars_path)

    def apply(self):
        """Apply the workload to the environment."""
        # Loaded configerus config for the plugin. Ready for .get().
        plugin_config = self._environment.config().load(self._config_label)

        playbook_contents: str = plugin_config.get(
            [self._config_base, ANSIBLE_WORKLOAD_CONFIG_PLAYBOOK_KEY], default={}
        )
        playbook_path: str = plugin_config.get(
            [self._config_base, ANSIBLE_WORKLOAD_CONFIG_PLAYBOOK_PATH_KEY],
            default="",
        )
        envs: Dict[str, str] = plugin_config.get(
            [self._config_base, ANSIBLE_WORKLOAD_CONFIG_ENVS_KEY], default={}
        )
        vars_values: str = plugin_config.get(
            [self._config_base, ANSIBLE_WORKLOAD_CONFIG_PLAYBOOK_VARS_KEY], default={}
        )
        vars_path: str = plugin_config.get(
            [self._config_base, ANSIBLE_WORKLOAD_CONFIG_PLAYBOOK_VARS_PATH_KEY],
            default="",
        )

        if playbook_contents:
            os.makedirs(os.path.dirname(os.path.realpath(playbook_path)), exist_ok=True)
            with open(playbook_path, "w", encoding="utf8") as playbook_fileobject:
                yaml.safe_dump(playbook_contents, playbook_fileobject)
        else:
            if playbook_path and os.path.exists(playbook_path):
                os.remove(playbook_path)
        if vars_values:
            os.makedirs(os.path.dirname(os.path.realpath(vars_path)), exist_ok=True)
            with open(vars_path, "w", encoding="utf8") as vars_fileobject:
                yaml.safe_dump(vars_values, vars_fileobject)
        else:
            if vars_path and os.path.exists(vars_path):
                os.remove(vars_path)

        return self._ansibleplaybook_client.run_file(
            playbooksyml_path=playbook_path, extravars_path=vars_path, envs=envs
        )
