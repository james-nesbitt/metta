"""

Test that some clients work

"""
import json
import logging

from mirantis.testing.metta.plugin import Type
from mirantis.testing.metta_kubernetes import METTA_PLUGIN_ID_KUBERNETES_CLIENT

logger = logging.getLogger("test_clients")

DEFAULT_K8S_NAMESPACE = 'default'


def test_launchpad_kubectl_client(environment_up):
    """ did we get a good kubectl client """

    logger.info("Getting K8s client")
    kubectl_client = environment_up.fixtures.get_plugin(type=Type.CLIENT,
                                                        plugin_id=METTA_PLUGIN_ID_KUBERNETES_CLIENT)

    coreV1 = kubectl_client.get_CoreV1Api_client()
    ns = coreV1.read_namespace(name=DEFAULT_K8S_NAMESPACE)
    print("NS: {}".format(ns))

    assert ns.metadata.name == DEFAULT_K8S_NAMESPACE, "Wrong namespace given"


def test_kubernetes_deployment_workload(environment_up, benchmark):
    """ test that we can get a k8s deployment workload to run """

    sanity_kubernetes_deployment = environment_up.fixtures.get_plugin(type=Type.WORKLOAD,
                                                                      instance_id='sanity_kubernetes_deployment')
    """ workload plugin """

    instance = sanity_kubernetes_deployment.create_instance(
        environment_up.fixtures)

    deployment = benchmark( instance.apply() )
    assert deployment is not None
    print(deployment.metadata.name)

    status = instance.destroy()
    assert status is not None
    assert status.code is None
    print(status)


def test_kubernetes_helm_workload(environment_up, benchmark):
    """ test that we can get a helm workload to run """

    metrics_helm_workload = environment_up.fixtures.get_plugin(type=Type.WORKLOAD,
                                                               instance_id='metrics-helm-workload')
    """ workload plugin """

    instance = metrics_helm_workload.create_instance(
        environment_up.fixtures)

    try:
        benchmark( instance.apply(wait=True) )
        instance.test()

        status = instance.status()

        assert status['name'] == instance.name
        assert status['info']['status'] == 'deployed'

        logger.info(json.dumps(status['info'], indent=2))

    except Exception as e:
        logger.error("helm operations failed: {}".format(e))

    instance.destroy()
