import logging
from typing import Dict, Any, List

import paramiko
import winrm

from mirantis.testing.metta_health.healthcheck import Health

logger = logging.getLogger("metta_nodes.node")


class HostNode:
    """A host that can act as a node in a cluster."""

    def __init__(self, client_id: str, host_id: str):
        """Make a node object from the configuration for a node."""
        self._interfaces: List[str] = []
        """String key-value labels for the node."""

        self._client_id = client_id
        self._host_id = host["id"]

    # pylint: disable=unused-argument
    def info(self, deep: bool = False) -> Dict[str, Any]:
        """Return structured information for introspection."""
        return {"id": self._host_id, "client_id": self._client_id, "interfaces": self._interfaces}

    def health(self) -> Health:
        """Evaluate health of the node."""
        return Health(source=f"{self._client_id}-{self._id}")


class SSHHostNode:
    """A host that can act as a node in a cluster that can accept ssh connections."""

    def __init__(self, client_id: str, host_id: str, ssh: Dict[str, str]):
        """Make a node object from the configuration for a node."""
        super().__init__(client_id, host_id)

        self._ssh: Dict[str, str] = ssh
        self._interfaces["ssh"] = True

    def info(self, deep: bool = False) -> Dict[str, Any]:
        """Return structured information for introspection."""
        info = super().info(deep=deep)
        info["ssh"] = self._ssh
        return info

    def health(self) -> Health:
        """Evaluate health of the node."""
        health = super().health()

        # Do some stuff here
        return health

    def execute(self, cmds: List[str]):
        """Execute a command on the hosts."""
        return self._ssh(cmds)

    def _ssh(self, cmds: List[str]) -> (str, str, str):
        """Execute a command using ssh."""
        ssh_config = self._ssh
        """Node object's ssh settings."""

        ssh_client = paramiko.SSHClient()

        k = paramiko.RSAKey.from_private_key_file(ssh_config["keyPath"])
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        ssh_client.connect(hostname=ssh_config["address"], username=ssh_config["user"], pkey=k)
        # ssh_stdin, ssh_stdout, ssh_stderr = ssh_client.exec_command(" ".join(cmds)))
        ssh_client.close()

        return ssh_stdin, ssh_stdout, ssh_stderr


class WinrmHostNode(HostNode):
    """A host that can act as a node in a cluster that accepts winrm connections."""

    def __init__(self, client_id: str, host_id: str, winrm: Dict[str, str]):
        """Make a node object from the configuration for a node."""
        super().__init__(client_id, host_id)

        self._winrm: Dict[str, str] = winrm
        self._interfaces["winrm"] = True

    def info(self, deep: bool = False) -> Dict[str, Any]:
        """Return structured information for introspection."""
        info = super().info(deep=deep)
        info["winrm"] = self._winrm
        return info

    def health(self) -> Health:
        """Evaluate health of the node."""
        health = super().health()

        # Do some stuff here

        return health

    def execute(self, cmds: List[str]):
        """Execute a command on the hosts."""
        return self._winrm(cmds)

    def _winrm(self, cmds: List[str]):
        """Execute a command using winrm."""
        winrm_config = self._winrm
        """Node object's winrm settings."""

        winrm_client = winrm.Session(
            winrm_config["address"], auth=(winrm_config["user"], winrm_config["password"])
        )
        r = s.run_cmd("ipconfig", ["/all"])
