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
    pass


@pytest.mark.order(2)
def test_kube_workload_still_running(environment_after_up):
    """ did we get a good kubectl client """

    logger.info(
        "Getting K8s test deployment which was run in the 'before' environment.")

    sanity_kubernetes_deployment = environment_after_up.fixtures.get_plugin(type=Type.WORKLOAD,
                                                                            instance_id='sanity_kubernetes_deployment')
    instance = sanity_kubernetes_deployment.create_instance(
        environment_after_up.fixtures)

    namespace = instance.namespace
    name = instance.name

    deployment = instance.read()
    assert deployment is not None, "Did not find the expected sanity workload running"
    print(deployment)

    status = deployment.status
    assert status is not None
    print(status)

    status = instance.destroy()
    assert status is not None
    assert status.code is None
    print(status)
