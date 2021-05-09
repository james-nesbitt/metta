"""

Test that some clients work

"""

import logging

import docker.models.containers

from mirantis.testing.metta.plugin import Type
from mirantis.testing.metta_docker import METTA_PLUGIN_ID_DOCKER_CLIENT

logger = logging.getLogger("test_mirantis_clients")


def test_launchpad_docker_client(environment_up):
    """ did we get a good docker client ? """
