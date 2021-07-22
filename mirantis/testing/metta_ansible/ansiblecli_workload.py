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
from mirantis.testing.metta.fixtures import Fixtures

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
ANSIBLE_WORKLOAD_CONFIG_ENVS_KEY = "env"
"""Configerus key for loading env variables to be used for clients."""
ANSIBLE_WORKLOAD_CONFIG_PLAYBOOK_KEY = "playbook.contents"
"""Configerus key for loading playbook groups/content."""
ANSIBLE_WORKLOAD_CONFIG_PLAYBOOK_PATH_KEY = "playbook.path"
"""Configerus key for finding what path to use for writing the playbook yaml."""


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

    def prepare(self, fixtures: Fixtures = None):
        """Find the dependent fixtures."""
        if fixtures is None:
            fixtures = self._environment.fixtures

        self._ansible_client = fixtures.get_plugin(
            plugin_id=METTA_ANSIBLE_ANSIBLECLI_CORECLIENT_PLUGIN_ID
        )

    def apply(self):
        """Apply the workload to the environment."""
        plugin_config = self._environment.config.load(self._config_label)
        """Loaded configerus config for the plugin. Ready for .get()."""

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

    def prepare(self, fixtures: Fixtures = None):
        """Find the dependent fixtures."""
        if fixtures is None:
            fixtures = self._environment.fixtures

        self._ansibleplaybook_client = fixtures.get_plugin(
            plugin_id=METTA_ANSIBLE_ANSIBLECLI_PLAYBOOKCLIENT_PLUGIN_ID
        )

    def apply(self):
        """Apply the workload to the environment."""
        plugin_config = self._environment.config.load(self._config_label)
        """Loaded configerus config for the plugin. Ready for .get()."""

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

        if playbook_contents:
            os.makedirs(os.path.dirname(os.path.realpath(playbook_path)), exist_ok=True)
            with open(playbook_path, "w") as playbook_fileobject:
                yaml.safe_dump(playbook_contents, playbook_fileobject)
        else:
            if playbook_path and os.path.exists(playbook_path):
                os.remove(playbook_path)

        return self._ansibleplaybook_client.run_file(playbooksyml_path=playbook_path, envs=envs)
