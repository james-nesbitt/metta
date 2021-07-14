"""

Test that some clients work

Test the the launchpad provisioner gave us  good exec plugin.

"""

import logging
import json

import pytest

from mirantis.testing.metta_launchpad import METTA_LAUNCHPAD_EXEC_CLIENT_PLUGIN_ID

logger = logging.getLogger("test_clients.launchpad_exec")


@pytest.fixture(scope="module")
def launchpad_exec_client(environment_up):
    """Get the launchpad exec plugin."""
    return environment_up.fixtures.get_plugin(
        plugin_id=METTA_LAUNCHPAD_EXEC_CLIENT_PLUGIN_ID
    )


def test_launchpad_exec_client_hosts(launchpad_exec_client):
    """do we get good hosts info from the client ?"""
    hosts = launchpad_exec_client.hosts()
    assert len(hosts) == 5

    logger.info("-> Dumping host list: %s", json.dumps(hosts, indent=2))


def test_launchpad_exec_client_exec(launchpad_exec_client):
    """did we get a good launchpad exec client ?"""
    logger.info("Running 'ls -la' on two different hosts")
    launchpad_exec_client.exec(host_index=0, cmds=["ls", "-la"])
    launchpad_exec_client.exec(host_index=2, cmds=["ls", "-la"])
    logger.info("Running docker cli with sudo on the first host")
    launchpad_exec_client.exec(
        host_index=0, cmds=["sudo", "docker", "container", "ps", "-a"]
    )
