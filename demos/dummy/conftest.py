import pytest

from mirantis.testing.metta import discover, get_environment
from mirantis.testing.metta.plugin import Type


@pytest.fixture(scope='session')
def environment_discover():
    """ discover the metta environment """
    # Tell metta to scan for automatic configuration of itself.
    # It starts my looking in paths upwards for a 'metta.yml' file; if it finds
    # one then it uses that path as a root source of config
    discover()


@pytest.fixture()
def environment(environment_discover):
    """ get the metta environment """
    # we don't use the discover fixture, we just need it to run first
    # we don't pass an environment name, which gives us the default environment
    return get_environment()


@pytest.fixture()
def provisioner(environment):
    """ get the first/default provisioner """
    return environment.fixtures.get_plugin(type=Type.PROVISIONER)


@pytest.fixture()
def workloads(environment):
    """ Get a set of workload fixtures """
    return environment.fixtures.get_fixtures(type=Type.WORKLOAD)
