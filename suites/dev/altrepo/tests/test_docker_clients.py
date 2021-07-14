"""

Test that some clients work

"""

import logging

logger = logging.getLogger("test_mirantis_clients")


# pylint: disable=unused-argument
def test_launchpad_docker_client(environment_up):
    """did we get a good docker client ?"""
