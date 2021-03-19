"""

Test that some clients work

"""

import logging
import pytest

from mirantis.testing.metta.plugin import Type

logger = logging.getLogger("mke_health")



def test_mke_api_ping(environment_up):
    """ did we get a good kubectl client """
