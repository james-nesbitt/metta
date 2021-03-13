"""

Test that helm workloads work

"""
import json
import logging
import time

from mirantis.testing.metta.plugin import Type
from mirantis.testing.metta_kubernetes import METTA_PLUGIN_ID_KUBERNETES_CLIENT
from mirantis.testing.metta_kubernetes.helm_workload import Status

logger = logging.getLogger("test_helm")

DEFAULT_K8S_NAMESPACE = 'default'


def test_kubernetes_helm_workload(environment_up, benchmark):
    """ test that we can get a helm workload to run """

    metrics_helm_workload = environment_up.fixtures.get_plugin(type=Type.WORKLOAD,
                                                               instance_id='metrics-helm-workload')
    """ workload plugin we will use to run helm """

    kubectl_client = environment_up.fixtures.get_plugin(type=Type.CLIENT,
                                                        plugin_id=METTA_PLUGIN_ID_KUBERNETES_CLIENT)
    appsV1 = kubectl_client.get_api('AppsV1Api')
    """ kubernetes client api we will use to detect the helm release in k8s """

    logger.info("Building the helm workload instance from the environment")
    instance = metrics_helm_workload.create_instance(
        environment_up.fixtures)

    # use some instance overrides
    # instance.name = "{}-{}".format(instance.name, 0)
    instance.namespace = DEFAULT_K8S_NAMESPACE

    try:

        list = instance.list()
        logger.info("Helm releases before start: {}".format(list))

        logger.info("Starting helm instance")
        instance.apply(wait=True)

        nsd = appsV1.list_namespaced_deployment(namespace=DEFAULT_K8S_NAMESPACE)
        logger.info("Namespace ({}) deployments: {}".format(DEFAULT_K8S_NAMESPACE, {item.metadata.name: item.status for item in nsd.items}))

        list = instance.list(all=True)
        logger.info("Helm release list before status: {}".format(list))

        deployment = appsV1.read_namespaced_deployment("{}-metrics-server".format(instance.name), instance.namespace)
        logger.info("Looks like the helm deployment: {}".format(deployment.metadata.annotations))

        logger.info("Running helm instance tests")
        instance.test()

        logger.info("Checking helm instance status")
        status = instance.status()
        assert status.name == instance.name
        assert status.status == Status.DEPLOYED
        logger.info("--> Status: {}".format(status.description))

    except Exception as e:
        logger.error("helm operations failed: {}".format(e))

    logger.info("Stopping the helm release instance")
    instance.destroy()
