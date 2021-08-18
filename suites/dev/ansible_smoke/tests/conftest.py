"""

Fixtures for the testing stack.

The parent scope conftest is focused on managing cluster resources, and this
focuses on fixtures used for the testing scope.

"""

import pytest

from mirantis.testing.metta_ansible.ansiblecli_client import (
    METTA_ANSIBLE_ANSIBLECLI_CORECLIENT_PLUGIN_ID,
)

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
    plugin = environment_up.fixtures().get_plugin(instance_id="healthpoller")

    plugin.prepare(environment_up.fixtures())
    plugin.apply()

    yield plugin

    plugin.destroy()


@pytest.fixture(scope="session")
def ansibleplaybook_provisioner(environment_up):
    """Retrieve the ansible provisioner plugin.

    This fixture makes no guarantee about provisioner/cluster state.

    Returns:
    --------
    An ansible provisioner plugin.

    """
    return environment_up.fixtures().get_plugin(instance_id="ansible")


@pytest.fixture(scope="session")
def ansible_client(environment_up):
    """Retrieve the ansible core client plugin

    This client will be created by the provisioner if all of the required information
    is available.

    Returns:
    --------
    An ansible cli client plugin.

    """
    return environment_up.fixtures().get_plugin(
        plugin_id=METTA_ANSIBLE_ANSIBLECLI_CORECLIENT_PLUGIN_ID
    )


@pytest.fixture(scope="session")
def ansibleplaybook_debugworkload(environment_up):
    """Retrieve the ansible playbook workload called "ansibledebug"

    Returns:
    --------
    An ansible playbook workload plugin.

    """
    plugin = environment_up.fixtures().get_plugin(instance_id="ansibledebug")
    plugin.prepare(fixtures=environment_up.fixtures())
    return plugin
