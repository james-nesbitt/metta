"""

Test that some clients work

"""

import logging
import pytest

from mirantis.testing.metta.plugin import Type

logger = logging.getLogger("test_start")


@pytest.mark.order(1)
def test_before_up(environment_before_up):
    """ confirm that phase 1 has started """
    logger.info("BEFORE: environment is confirmed up.")


@pytest.mark.order(1)
def test_kubernetes_deployment_workload(environment_before_up):
    """ test that we can get a k8s workload to run """
    logger.info(
        "Starting a kubernetes workload in this environment, so that we can confirm it is running after an upgrade.")

    sanity_kubernetes_deployment = environment_before_up.fixtures.get_plugin(type=Type.WORKLOAD,
                                                                             instance_id='sanity_kubernetes_deployment')
    """ workload plugin """

    instance = sanity_kubernetes_deployment.create_instance(
        environment_before_up.fixtures)

    deployment = instance.apply()
    assert deployment is not None
    logger.info("BEFORE: sanity workload deployed: {}".format(deployment))
