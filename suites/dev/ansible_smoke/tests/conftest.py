"""

Fixtures for the testing stack.

The parent scope conftest is focused on managing cluster resources, and this
focuses on fixtures used for the testing scope.

"""

import pytest


# impossible to chain pytest fixtures without using the same names
# pylint: disable=redefined-outer-name
# unused argument is their to force dependency hierarchy
# pylint: disable=unused-argument


@pytest.fixture(scope="session")
def healthpoller(environment_up):
    """Retrieve a healthpoller workload.

    @NOTE that this collects existing healthcheck instances available at the
        time of the creation of this fixture, so you should ask for it after
        you have generated all of the healtchecks desired.
        This often means creating any workload instances ahead of time.

    Returns:
    --------
    A started health-poller workload.

    """
    plugin = environment_up.fixtures.get_plugin(instance_id="healthpoller")

    plugin.prepare(environment_up.fixtures)
    plugin.apply()

    yield plugin

    plugin.destroy()


@pytest.fixture(scope="session")
def ansible_provisioner(environment_up):
    """Retrieve the ansible provisioner plugin.

    This fixture makes no guarantee about provisioner/cluster state.

    Returns:
    --------
    An ansible provisioner plugin.

    """
    plugin = environment_up.fixtures.get_plugin(instance_id="ansible")

    return plugin


@pytest.fixture(scope="session")
def ansible_play(ansible_provisioner):
    """Retrieve the ansible play object from the provisioner

    Returns:
    --------
    An ansible play object provisioner plugin.

    """
    # pylint: disable=protected-access
    return ansible_provisioner._ansible
