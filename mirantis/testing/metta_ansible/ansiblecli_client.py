"""

Metta client plugins for the ansible cli handlers.

"""

import logging
from typing import List, Dict

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta_health.healthcheck import Health

from .ansiblecli import AnsibleClient, AnsiblePlaybookClient

logger = logging.getLogger("metta.contrib.client:ansible")

METTA_ANSIBLE_ANSIBLECLI_CORECLIENT_PLUGIN_ID = "metta_ansible_clicore_ansible_client"
""" Ansible client plugin id """

METTA_ANSIBLE_ANSIBLECLI_PLAYBOOKCLIENT_PLUGIN_ID = "metta_ansible_clicore_ansibleplaybook_client"
""" Ansible-Playbook client plugin id """


# pylint: disable=too-many-instance-attributes
class AnsibleClientPlugin:
    """Ansible provisioner plugin.

    Client plugin that allows control of and interaction with a ansible
    cluster using ansible cli.

    ## Requirements

    1. this plugin uses subprocess to call a ansible binary, so you have to install
       ansible in the environment

    ## Usage

    """

    def __init__(
        self,
        environment: Environment,
        instance_id: str,
        inventory_path: str,
        ansiblecfg_path: str = "",
    ):
        """Initialize Ansible Playbook client.

        Parameters:
        -----------
        environment (Environment) : All metta plugins receive the environment
            object in which they were created.
        instance_id (str) : all metta plugins receive their own string identity.

        inventory_path (str) : string path to an inventory file.
        ansiblecfg_path (str) : string path to an optional ansiblecfg file.

        """
        self._environment: Environment = environment
        """Environemnt in which this plugin exists."""
        self._instance_id: str = instance_id
        """Unique id for this plugin instance."""

        self._ansible: AnsibleClient = AnsibleClient(
            ansiblecfg_path=ansiblecfg_path,
            inventory_path=inventory_path,
        )
        """Backend ansible cli handler."""

    # deep argument is an info() standard across plugins
    # pylint: disable=unused-argument
    def info(self, deep: bool = False):
        """Get info about a provisioner plugin."""
        return {
            "client": self._ansible.info(deep=deep) if self._ansible else "MISSING",
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

    def run(
        self,
        args: List[str],
        envs: Dict[str, str] = None,
        return_output: bool = False,
    ):
        """Run a set of string ansible arguments."""
        return self._ansible.run(args=args, envs=envs, return_output=return_output)

    def debug(self, hosts: str = "all"):
        """Run a set of string ansible arguments."""
        return self._ansible.debug(hosts=hosts)

    def setup(self, hosts: str = "all"):
        """Run a set of string ansible arguments."""
        return self._ansible.setup(hosts=hosts)

    def ping(self, hosts: str = "all"):
        """Run a set of string ansible arguments."""
        return self._ansible.ping(hosts=hosts)

    def _health_all_ping(self) -> Health:
        """Health check that tries to ping all of the hosts."""
        ping_health = Health(source=self._instance_id)

        ping = self.ping()

        try:
            ping_task_result_hosts = ping["plays"][0]["tasks"][0]["hosts"]
            stats_hosts = ping["stats"]
        except KeyError:
            ping_health.error("ansible ping gave unexpected results.")
        else:
            for host, host_stats in stats_hosts.items():
                if host_stats["ok"]:
                    ping_health.healthy(f"Ansible: {host} ping response ok.")
                elif host_stats["unreachable"]:
                    ping_health.warning(f"Ansible: {host} unreachable during ping.")
                elif host_stats["ignored"]:
                    ping_health.warning(f"Ansible: {host} ping ignored.")
                elif host_stats["failures"]:
                    ping_health.error(f"Ansible: {host} ping failed.")
                elif host_stats["unknowwn"]:
                    ping_health.error(f"Ansible: {host} ping skipped.")
                else:
                    ping_health.warning(
                        f"Ansible: {host} status not understood: {ping_task_result_hosts[host]}."
                    )

        return ping_health


# pylint: disable=too-many-instance-attributes
class AnsiblePlaybookClientPlugin:
    """Ansible Playbook client plugin.

    Client plugin that allows control of and interaction with a ansible
    cluster using ansible-playbook cli

    ## Requirements

    1. this plugin uses subprocess to call a ansible binary, so you have to install
       ansible in the environment

    ## Usage

    """

    def __init__(
        self,
        environment,
        instance_id,
        inventory_path: str,
        ansiblecfg_path: str = "",
    ):
        """Initialize Ansible Playbook client.

        Parameters:
        -----------
        environment (Environment) : All metta plugins receive the environment
            object in which they were created.
        instance_id (str) : all metta plugins receive their own string identity.

        inventory_path (str) : string path to an inventory file.
        ansiblecfg_path (str) : string path to an optional ansiblecfg file.

        """
        self._environment: Environment = environment
        """Environemnt in which this plugin exists."""
        self._instance_id: str = instance_id
        """Unique id for this plugin instance."""

        self._ansibleplaybook = AnsiblePlaybookClient(
            ansiblecfg_path=ansiblecfg_path,
            inventory_path=inventory_path,
        )
        """Backend ansible-playbook cli handler."""

    # deep argument is an info() standard across plugins
    # pylint: disable=unused-argument
    def info(self, deep: bool = False):
        """Get info about a provisioner plugin."""
        return {
            "client": self._ansibleplaybook.info(deep=deep)
            if self._ansibleplaybook
            else "MISSING",
        }

    # pylint: disable=too-many-arguments
    def run_file(
        self,
        playbooksyml_path: str,
        extravars_path: str = "",
        extravars: Dict[str, str] = None,
        envs: Dict[str, str] = None,
        return_output: bool = False,
    ):
        """Run the ansible playbook install command on a yaml playbook file."""
        return self._ansibleplaybook.run(
            playbooksyml_path=playbooksyml_path,
            extravars_path=extravars_path,
            extravars=extravars,
            envs=envs,
            return_output=return_output,
        )
