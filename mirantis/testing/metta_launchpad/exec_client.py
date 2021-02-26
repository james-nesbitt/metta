
import logging
from typing import List

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.client import ClientBase

from .launchpad import LaunchpadClient

logger = logging.getLogger('metta.contrib.kubernetes.client')


METTA_LAUNCHPAD_EXEC_CLIENT_PLUGIN_ID = "metta_launchpad_exec"


class LaunchpadExecClientPlugin(ClientBase):
    """ Client for exec into hosts using launchpad """

    def __init__(self, environment: Environment,
                 instance_id: str, client: LaunchpadClient):
        """

        Parameters:
        -----------

        client (LaunchpadClient) : A configured launchpad client to use to run
            exec commands

        """
        ClientBase.__init__(self, environment, instance_id)

        self.client = client

    def hosts(self, deep: bool = False):
        """ list the hosts in the cluster """

        config = self.client.describe_config()

        if deep:
            list = [host for host in config['spec']['hosts']]
        else:
            list = []
            for host in config['spec']['hosts']:
                list_host = {
                    'role': host['role']
                }
                if 'ssh' in host:
                    list_host.update({
                        'is_windows': False,
                        'address': host['ssh']['address']
                    })
                if 'winrm' in host:
                    list_host.update({
                        'is_windows': True,
                        'address': host['winrm']['address']
                    })

                list.append(list_host)

        return list

    def exec(self, cmds: List[str], host_index: int):
        """ Exec a string arg list command on a single host """

        client_config = self.client.describe_config()
        hosts = client_config['spec']['hosts']
        host = hosts[host_index]

        return self.client.exec(host_index, cmds)
