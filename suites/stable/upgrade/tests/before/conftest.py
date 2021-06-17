"""

PyTest preparation for the before environment.

Fixtures usable in the before upgrade state.

"""
import pytest

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.workload import METTA_PLUGIN_TYPE_WORKLOAD

from mirantis.testing.metta_kubernetes.deployment_workload import (
    KubernetesDeploymentWorkloadPlugin, KubernetesDeploymentWorkloadInstance)

# impossible to chain pytest fixtures without using the same names
# pylint: disable=redefined-outer-name
# unused argument is their to force dependency hierarchy
# pylint: disable=unused-argument


@pytest.fixture(scope='module')
def stability_workload(environment_before_up: Environment) -> KubernetesDeploymentWorkloadPlugin:
    """Get the stability kubernetes deployment workload."""
    return environment_before_up.fixtures.get_plugin(
        plugin_type=METTA_PLUGIN_TYPE_WORKLOAD,
        instance_id='stability_deployment')


@pytest.fixture(scope='module')
def stability_workload_instance(
    environment_before_up: Environment,
    stability_workload: KubernetesDeploymentWorkloadPlugin) -> KubernetesDeploymentWorkloadInstance:
    """Get a workload instance from the stability workload plugin."""
    return stability_workload.create_instance(
        environment_before_up.fixtures)
