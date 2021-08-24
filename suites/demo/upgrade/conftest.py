"""

PyTest setup for test suite

Primarily used to define fixtures used for the pytest implementation, which are then consumed by
the test cases themselved.

We realy heavily on metta discovery which looks for the metta.yml file, and uses that to interpret
the config folder to define metta infrastructure.  The same approach is used by the metta cli,
which makes the cli quite usable in this scope

"""
import logging

import pytest

from mirantis.testing.metta import discover, get_environment, Environment


logger = logging.getLogger("pytest-conftest")

""" Define our fixtures """

# impossible to chain pytest fixtures without using the same names
# pylint: disable=redefined-outer-name
# unused argument is their to force dependency hierarchy
# pylint: disable=unused-argument


@pytest.fixture(scope="session")
def environment_discover():
    """discover the metta environments"""
    # Tell metta to scan for automatic configuration of itself.
    # It starts my looking in paths upwards for a 'metta.yml' file; if it finds
    # one then it uses that path as a root source of config
    discover()


@pytest.fixture(scope="session")
def environment(environment_discover) -> Environment:
    """get the metta environment"""
    # we don't use the discover fixture, we just need it to run first
    # we don't pass an environment name, which gives us the default environment
    return get_environment()
