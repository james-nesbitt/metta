"""

PyTest preparation for the after environment.

Fixtures usable in the after upgrade state.

"""
import pytest

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.client import METTA_PLUGIN_TYPE_CLIENT
from mirantis.testing.metta.workload import METTA_PLUGIN_TYPE_WORKLOAD

from mirantis.testing.metta_kubernetes.deployment_workload import (
    KubernetesDeploymentWorkloadPlugin,
    KubernetesDeploymentWorkloadInstance,
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
        plugin_type=METTA_PLUGIN_TYPE_WORKLOAD, instance_id="stability_deployment"
    )


@pytest.fixture(scope="module")
def stability_workload_instance(
    environment_after_up: Environment,
    stability_workload: KubernetesDeploymentWorkloadPlugin,
) -> KubernetesDeploymentWorkloadInstance:
    """Get a workload instance from the stability workload plugin."""
    return stability_workload.create_instance(environment_after_up.fixtures)


@pytest.fixture(scope="module")
def mke_client(environment_after_up: Environment) -> MKEAPIClientPlugin:
    """Get the mke client."""
    return environment_after_up.fixtures.get_plugin(
        plugin_type=METTA_PLUGIN_TYPE_CLIENT,
        plugin_id=METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID,
    )


@pytest.fixture(scope="module")
def msr_client(environment_after_up: Environment) -> MSRAPIClientPlugin:
    """Get the msr client."""
    return environment_after_up.fixtures.get_plugin(
        plugin_type=METTA_PLUGIN_TYPE_CLIENT,
        plugin_id=METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID,
    )
