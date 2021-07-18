"""

Test that teh MKE client works

"""

import logging


logger = logging.getLogger("test_msr")

# this is a test suite, and lazy interpolation is not very strong
# pylint: disable=logging-format-interpolation


def test_environment_is_up(environment_up):
    """did we an up environment"""
    pass
