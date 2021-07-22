"""

ansible cli handler.

Here are is all of the functionality which actually runs ansible commands
on the command line using subprocess.

"""

import logging
import json
import os
import subprocess
import shutil
from typing import Dict, List, Any

logger = logging.getLogger("metta_ansible:ansible-cli")

ANSIBLE_CLIENT_DEFAULT_BINARY = "ansible"
""" default ansible executable for subprocess """
ANSIBLEPLAYBOOK_CLIENT_DEFAULT_BINARY = "ansible-playbook"
""" default ansible-playbook executable for subprocess """

METTA_ANSIBLE_ANSIBLECLI_ENV_JSONOUT = {
    "ANSIBLE_STDOUT_CALLBACK": "json",
    "ANSIBLE_LOAD_CALLBACK_PLUGINS": "1",
}
"""Passing these env vars to ansible will give us json output."""


class AnsibleClient:
    """Shell client for running ansible-playbook using subprocess."""

    # this is what it takes to configure the terraform client
    # pylint: disable=too-many-arguments
    def __init__(
        self,
        inventory_path: str,
        ansiblecfg_path: str,
        ansiblebinary: str = ANSIBLE_CLIENT_DEFAULT_BINARY,
    ):
        """Initialize Ansible client.

        Parameters:
        -----------

        """
        self.inventory_path = inventory_path
        self.ansiblecfg_path = ansiblecfg_path

        if shutil.which(ansiblebinary) is None:
            raise ValueError(
                "Ansible binary not found. Ansible commands cannot be called. "
                f"Expected binary at path {ansiblebinary}"
            )

        self.ansible_bin = ansiblebinary

    # deep argument is a part of the info() interface for all plugins
    # pylint: disable=unused-argument
    def info(self, deep: bool = False) -> Dict[str, Any]:
        """Return dict of plugin info for introspection."""
        return {
            "inventory_path": self.inventory_path,
            "ansiblecfg_path": self.ansiblecfg_path,
        }

    def debug(self, hosts: str = "all"):
        """Run ansible debug and return parsed response."""
        return json.loads(
            self.run(
                ["--module-name=debug", hosts],
                envs=METTA_ANSIBLE_ANSIBLECLI_ENV_JSONOUT,
                return_output=True,
            )
        )

    def setup(self, hosts: str = "all"):
        """Run ansible setup and return parsed response."""
        return json.loads(
            self.run(
                ["--module-name=setup", hosts],
                envs=METTA_ANSIBLE_ANSIBLECLI_ENV_JSONOUT,
                return_output=True,
            )
        )

    def ping(self, hosts: str = "all"):
        """Run ansible ping and return parsed response."""
        return json.loads(
            self.run(
                ["--module-name=ping", hosts],
                envs=METTA_ANSIBLE_ANSIBLECLI_ENV_JSONOUT,
                return_output=True,
            )
        )

    def run(
        self,
        args: List[str],
        envs: Dict[str, str] = None,
        with_inventory=True,
        with_ansiblecfg=True,
        return_output=False,
    ):
        """Run ansible CLI command."""
        env = os.environ.copy()

        cmd = [self.ansible_bin]

        if with_ansiblecfg:
            env["ANSIBLE_CONFIG"] = self.ansiblecfg_path
        if with_inventory:
            cmd += [f"--inventory={self.inventory_path}"]
        if envs is not None:
            env.update(envs)

        cmd += args

        # improve readability
        # pylint: disable=no-else-return
        if not return_output:
            logger.debug("running ansible command: %s", " ".join(cmd))
            res = subprocess.run(cmd, env=env, check=True, text=True)
            res.check_returncode()
            return res
        else:
            logger.debug("running ansible command with output capture: %s", " ".join(cmd))
            res = subprocess.run(cmd, env=env, shell=False, check=True, stdout=subprocess.PIPE)
            res.check_returncode()
            return res.stdout.decode("utf-8")


class AnsiblePlaybookClient:
    """Shell client for running ansible-playbook using subprocess."""

    # this is what it takes to configure the terraform client
    # pylint: disable=too-many-arguments
    def __init__(
        self,
        inventory_path: str,
        ansiblecfg_path: str,
        playbookbinary: str = ANSIBLEPLAYBOOK_CLIENT_DEFAULT_BINARY,
    ):
        """Initialize Ansible Playbook client.

        Parameters:
        -----------

        """
        self.inventory_path = inventory_path
        self.ansiblecfg_path = ansiblecfg_path

        if shutil.which(playbookbinary) is None:
            raise ValueError(
                "Ansible-Playbook binary not found. Ansible commands cannot be called. "
                f"Expected binary at path {playbookbinary}"
            )

        self.ansibleplaybook_bin = playbookbinary

    # deep argument is a part of the info() interface for all plugins
    # pylint: disable=unused-argument
    def info(self, deep: bool = False) -> Dict[str, Any]:
        """Return dict of plugin info for introspection."""
        return {
            "inventory_path": self.inventory_path,
            "ansiblecfg_path": self.ansiblecfg_path,
        }

    def run(self, playbooksyml_path: str):
        """Run the ansible playbook install command on a yaml playbook file."""
        args = [playbooksyml_path]

        return self._run(args)

    def _run(
        self,
        args: List[str],
        with_inventory=True,
        with_ansiblecfg=True,
        return_output=False,
    ):
        """Run ansible-playbook CLI command."""
        env = os.environ.copy()

        cmd = [self.ansibleplaybook_bin]

        if with_ansiblecfg:
            env["ANSIBLE_CONFIG"] = self.ansiblecfg_path
        if with_inventory:
            cmd += [f"--inventory={self.inventory_path}"]

        cmd += args

        # improve readability
        # pylint: disable=no-else-return
        if not return_output:
            logger.debug("running ansible-playbook command: %s", " ".join(cmd))
            res = subprocess.run(cmd, env=env, check=True, text=True)
            res.check_returncode()
            return res
        else:
            logger.debug("running ansible-playbook command with output capture: %s", " ".join(cmd))
            res = subprocess.run(cmd, env=env, shell=False, check=True, stdout=subprocess.PIPE)
            res.check_returncode()
            return res.stdout.decode("utf-8")
