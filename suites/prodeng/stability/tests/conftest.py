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
def nginx_deployment(environment_up):
    """Get the k8s deployment called nginx-k8s-workload."""
    # check fixtures.yml for 'nginx-k8s-deployment'
    plugin = environment_up.fixtures.get_plugin(
        instance_id="nginx-k8s-deployment"
    )

    plugin.prepare(environment_up.fixtures)
    plugin.apply()

    yield plugin

    plugin.destroy()


@pytest.fixture(scope="session")
def metrics_deployment(environment_up):
    """Get the helm deployment called metrics-helm-workload."""
    # check fixtures.yml for 'metrics-helm-workload'
    plugin = environment_up.fixtures.get_plugin(
        instance_id="metrics-helm-workload"
    )

    plugin.prepare(environment_up.fixtures)
    plugin.apply()

    yield plugin

    plugin.destroy()


@pytest.fixture()
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
