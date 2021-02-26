import pytest

from mirantis.testing.metta import get_environment
from mirantis.testing.metta.plugin import Type

from .metta import ENVIRONMENT_NAME


@pytest.fixture()
def environment():
    """ get the metta environment """
    return get_environment(ENVIRONMENT_NAME)


@pytest.fixture()
def provisioner(environment):
    """ get the first/default provisioner """
    return environment.fixtures.get_plugin(type=Type.PROVISIONER)


@pytest.fixture()
def workloads(environment):
    """ Get a set of workload fixtures """
    return environment.fixtures.get_fixtures(type=Type.WORKLOAD)
