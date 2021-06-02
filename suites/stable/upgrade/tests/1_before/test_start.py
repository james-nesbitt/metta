"""

Test that some clients work

"""

import logging

import pytest

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.workload import METTA_PLUGIN_TYPE_WORKLOAD

logger = logging.getLogger("test_start")


# pylint: disable=unused-argument
@pytest.mark.order(1)
def test_before_up(environment_before_up: Environment):
    """ confirm that phase 1 has started """
    logger.info("BEFORE: environment is confirmed up.")


@pytest.mark.order(1)
def test_kubernetes_deployment_workload(environment_before_up: Environment):
    """ test that we can get a k8s workload to run """
    logger.info("Starting a kubernetes workload in this environment, so that we can "
                "confirm it is running after an upgrade.")

    sanity_kubernetes_deployment = environment_before_up.fixtures.get_plugin(
        plugin_type=METTA_PLUGIN_TYPE_WORKLOAD,
        instance_id='sanity_kubernetes_deployment')
    """ workload plugin (instance_id must match our config/fixtures.yml key)"""

    instance = sanity_kubernetes_deployment.create_instance(
        environment_before_up.fixtures)

    namespace = instance.namespace
    name = instance.name

    deployment = instance.apply()
    assert deployment is not None
    logger.info("BEFORE: sanity workload deployed: %s}", deployment)

    metadata = deployment.metadata
    assert name == metadata.name
    assert namespace == metadata.namespace
