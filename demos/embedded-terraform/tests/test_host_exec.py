"""

Test that some clients work

"""

import logging
import json

from mirantis.testing.metta.plugin import Type
from mirantis.testing.metta_launchpad import METTA_LAUNCHPAD_EXEC_CLIENT_PLUGIN_ID

logger = logging.getLogger("test_clients")


def test_launchpad_exec_client_hosts(environment_up):
    """ do we get good hosts info from the client ? """

    logger.info("Getting exec client")
    exec_client = environment_up.fixtures.get_plugin(type=Type.CLIENT,
                                                     plugin_id=METTA_LAUNCHPAD_EXEC_CLIENT_PLUGIN_ID)

    hosts = exec_client.hosts()
    assert len(hosts) > 0

    print(json.dumps(hosts, indent=2))


def test_launchpad_exec_client_exec(environment_up):
    """ did we get a good launchpad exec client ? """
    logger.info("Getting exec client")
    exec_client = environment_up.fixtures.get_plugin(type=Type.CLIENT,
                                                     plugin_id=METTA_LAUNCHPAD_EXEC_CLIENT_PLUGIN_ID)

    exec_client.exec(host_index=0, cmds=['ls', '-la'])
    exec_client.exec(
        host_index=0,
        cmds=[
            'sudo',
            'docker',
            'container',
            'ps',
            '-a'])
    exec_client.exec(host_index=2, cmds=['ls', '-la'])
