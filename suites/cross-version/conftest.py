import pytest
import logging

from mirantis.testing.metta import discover, get_environment
from mirantis.testing.metta.plugin import Type

logger = logging.getLogger('sanity-suite')

""" Define our fixtures """


@pytest.fixture(scope='session', autouse=True)
def environment_discover():
    """ discover the metta environments """
    # Tell metta to scan for automatic configuration of itself.
    # It starts my looking in paths upwards for a 'metta.yml' file; if it finds
    # one then it uses that path as a root source of config
    discover()
