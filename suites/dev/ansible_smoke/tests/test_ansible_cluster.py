"""

Test that the ansible provisioner works

"""

import logging

from mirantis.testing.metta_common.healthpoll_workload import health_poller_output_log
from mirantis.testing.metta_cli.base import cli_output

logger = logging.getLogger("test_ansible")


# jsut receiving the environment fixture validates our environment
# pylint: disable=unused-argument
def test_001_environment_is_up(environment_up):
    """did we an up environment"""


def test_002_run_playbook(ansibleplaybook_debugworkload):
    """Can we run a playbook workload."""
    ansibleplaybook_debugworkload.apply()


def test_003_play_with_ansible_client(ansible_client):
    """Run some of the ansible client methods to make sure that they work."""

    print(cli_output(ansible_client.setup()))
    print(cli_output(ansible_client.ping()))
    print(cli_output(ansible_client.debug()))


def test_004_health_is_up(healthpoller):
    """Is the cluster healthy after 60 seconds."""
    poll_logger = logger.getChild("healthpoller")
    """Use a new logger just for the health output."""

    # use a common function for logging poller status
    health_poller_output_log(healthpoller=healthpoller, poll_logger=poll_logger, period=60, count=1)
