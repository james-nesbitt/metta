"""

Test that some clients work

"""

import logging
import json

from mirantis.testing.metta.client import METTA_PLUGIN_INTERFACE_ROLE_CLIENT
from mirantis.testing.metta_launchpad import METTA_LAUNCHPAD_EXEC_CLIENT_PLUGIN_ID

logger = logging.getLogger("test_clients")

# this is a test suite, and lazy interpolation is not very strong
# pylint: disable=logging-format-interpolation


def test_launchpad_exec_client_hosts(environment_up):
    """do we get good hosts info from the client ?"""

    logger.info("Getting exec client")
    exec_client = environment_up.fixtures.get_plugin(
        plugin_type=METTA_PLUGIN_INTERFACE_ROLE_CLIENT,
        plugin_id=METTA_LAUNCHPAD_EXEC_CLIENT_PLUGIN_ID,
    )

    hosts = exec_client.hosts()
    assert len(hosts) == 5

    dump = json.dumps(hosts, indent=2)
    logger.info("-> Dumping host list: {dump}")


def test_launchpad_exec_client_exec(environment_up):
    """did we get a good launchpad exec client ?"""
    logger.info("Getting exec client")
    exec_client = environment_up.fixtures.get_plugin(
        plugin_type=METTA_PLUGIN_INTERFACE_ROLE_CLIENT,
        plugin_id=METTA_LAUNCHPAD_EXEC_CLIENT_PLUGIN_ID,
    )

    logger.info("Running 'ls -la' on two different hosts")
    exec_client.exec(host_index=0, cmds=["ls", "-la"])
    exec_client.exec(host_index=2, cmds=["ls", "-la"])
    logger.info("Runnign docker cli with sudo on the first host")
    exec_client.exec(host_index=0, cmds=["sudo", "docker", "container", "ps", "-a"])
