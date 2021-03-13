"""

Test that some clients work

"""

import logging
import pytest

from mirantis.testing.metta.plugin import Type

logger = logging.getLogger("test_stop")


@pytest.mark.order(2)
def test_after_up(environment_after_up):
    """ confirm that phase 2 has started """
    logger.info("AFTER: environment is confirmed up.")


@pytest.mark.order(2)
def test_kube_workload_still_running(environment_after_up):
    """ did we get a good kubectl client """

    logger.info(
        "AFTER: Getting K8s test deployment which was run in the 'before' environment.")

    sanity_kubernetes_deployment = environment_after_up.fixtures.get_plugin(type=Type.WORKLOAD,
                                                                            instance_id='sanity_kubernetes_deployment')
    instance = sanity_kubernetes_deployment.create_instance(
        environment_after_up.fixtures)

    namespace = instance.namespace
    name = instance.name

    # The start test sshould have created this workload, so we should be able
    # to find it.
    deployment = instance.read()
    assert deployment is not None, "Did not find the expected sanity workload running"
    logger.info(deployment)

    status = deployment.status
    assert status is not None
    logger.info("Sanity deployment status: {}".format(status))
    metadata = deployment.metadata
    assert name == metadata.name
    assert namespace == metadata.namespace

    # tear the deployment down
    status = instance.destroy()
    assert status is not None
    assert status.code is None
    logger.info("Sanity deployment destroy status: {}".format(status))
