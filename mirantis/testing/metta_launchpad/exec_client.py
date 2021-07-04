"""

Metta client plugin for executing commands (ssh/winrm) on hosts provisioned.

On a cluster of hosts provisioned using the Launchpad provisioner, execute
a command over ssh/winrm on one of the hosts.

"""
import logging
from typing import List

from mirantis.testing.metta.environment import Environment

from .launchpad import LaunchpadClient

logger = logging.getLogger("metta.contrib.kubernetes.client")


METTA_LAUNCHPAD_EXEC_CLIENT_PLUGIN_ID = "metta_launchpad_exec_client"
""" metta plugin ID for the metta exec client plugin """


class LaunchpadExecClientPlugin:
    """Client for exec into hosts using launchpad."""

    def __init__(
        self, environment: Environment, instance_id: str, client: LaunchpadClient
    ):
        """Create launchpad exec plugin.

        Parameters:
        -----------
        client (LaunchpadClient) : A configured launchpad client to use to run
            exec commands

        """
        self._environment = environment
        """ Environemnt in which this plugin exists """
        self._instance_id = instance_id
        """ Unique id for this plugin instance """

        self.client = client
        """ Launchpad client """

    def hosts(self, deep: bool = False):
        """List the hosts in the cluster."""
        config = self.client.describe_config()

        if deep:
            host_list = list(config["spec"]["hosts"])
        else:
            host_list = []
            for host in config["spec"]["hosts"]:
                list_host = {"role": host["role"]}
                if "ssh" in host:
                    list_host.update(
                        {"is_windows": False, "address": host["ssh"]["address"]}
                    )
                if "winrm" in host:
                    list_host.update(
                        {"is_windows": True, "address": host["winrm"]["address"]}
                    )

                host_list.append(list_host)

        return host_list

    def exec(self, cmds: List[str], host_index: int):
        """Exec a string arg list command on a single host."""
        return self.client.exec(host_index, cmds)
