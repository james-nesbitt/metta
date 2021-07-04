"""

PyTest preparation for the after environment.

Fixtures usable in the after upgrade state.

"""
import pytest

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.client import METTA_PLUGIN_INTERFACE_ROLE_CLIENT
from mirantis.testing.metta.workload import METTA_PLUGIN_INTERFACE_ROLE_WORKLOAD

from mirantis.testing.metta_kubernetes.deployment_workload import (
    KubernetesDeploymentWorkloadPlugin,
)

from mirantis.testing.metta_mirantis.mke_client import (
    MKEAPIClientPlugin,
    METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID,
)
from mirantis.testing.metta_mirantis.msr_client import (
    MSRAPIClientPlugin,
    METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID,
)

# impossible to chain pytest fixtures without using the same names
# pylint: disable=redefined-outer-name
# unused argument is their to force dependency hierarchy
# pylint: disable=unused-argument


@pytest.fixture(scope="module")
def stability_workload(
    environment_after_up: Environment,
) -> KubernetesDeploymentWorkloadPlugin:
    """Get the stability kubernetes deployment workload."""
    return environment_after_up.fixtures.get_plugin(
        interfaces=[METTA_PLUGIN_INTERFACE_ROLE_WORKLOAD],
        instance_id="stability_deployment",
    )


@pytest.fixture(scope="module")
def stability_workload_up(
    environment_before_up: Environment,
    stability_workload: KubernetesDeploymentWorkloadPlugin,
) -> KubernetesDeploymentWorkloadPlugin:
    """Get a workload instance from the stability workload plugin."""
    stability_workload.prepare(environment_before_up.fixtures)
    return stability_workload


@pytest.fixture(scope="module")
def mke_client(environment_after_up: Environment) -> MKEAPIClientPlugin:
    """Get the mke client."""
    return environment_after_up.fixtures.get_plugin(
        interfaces=[METTA_PLUGIN_INTERFACE_ROLE_CLIENT],
        plugin_id=METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID,
    )


@pytest.fixture(scope="module")
def msr_client(environment_after_up: Environment) -> MSRAPIClientPlugin:
    """Get the msr client."""
    return environment_after_up.fixtures.get_plugin(
        interfaces=[METTA_PLUGIN_INTERFACE_ROLE_CLIENT],
        plugin_id=METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID,
    )
