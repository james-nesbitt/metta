"""

Test that helm workloads work

"""
import logging

from mirantis.testing.metta.client import METTA_PLUGIN_TYPE_CLIENT
from mirantis.testing.metta.workload import METTA_PLUGIN_TYPE_WORKLOAD

from mirantis.testing.metta_kubernetes import METTA_PLUGIN_ID_KUBERNETES_CLIENT
from mirantis.testing.metta_kubernetes.helm_workload import Status

logger = logging.getLogger("test_helm")

DEFAULT_K8S_NAMESPACE = "default"


def test_kubernetes_helm_workload(environment_up):
    """Test that we can get a helm workload to run."""

    metrics_helm_workload = environment_up.fixtures.get_plugin(
        plugin_type=METTA_PLUGIN_TYPE_WORKLOAD, instance_id="metrics-helm-workload"
    )
    """ workload plugin we will use to run helm """

    kubectl_client = environment_up.fixtures.get_plugin(
        plugin_type=METTA_PLUGIN_TYPE_CLIENT,
        plugin_id=METTA_PLUGIN_ID_KUBERNETES_CLIENT,
    )
    """ kubeapi client plugin """

    apps_v1 = kubectl_client.get_api("AppsV1Api")
    """ kubernetes client api we will use to detect the helm release in k8s """

    logger.info("Building the helm workload instance from the environment")
    instance = metrics_helm_workload.create_instance(environment_up.fixtures)

    # use some instance overrides
    # instance.name = f"{instance.name}-{0}""
    instance.namespace = DEFAULT_K8S_NAMESPACE

    try:
        instance_list = instance.list()
        logger.info("Helm releases before start: %s", instance_list)

        logger.info("Starting helm instance")
        instance.apply(wait=True)

        nsd = apps_v1.list_namespaced_deployment(namespace=DEFAULT_K8S_NAMESPACE)
        logger.info(
            "Namespace (%s) deployments: %s",
            DEFAULT_K8S_NAMESPACE,
            {item.metadata.name: item.status for item in nsd.items},
        )

        instance_list = instance.list(all=True)
        logger.info("Helm release list before status: %s", instance_list)

        deployment = apps_v1.read_namespaced_deployment(
            f"{instance.name}-metrics-server", instance.namespace
        )
        logger.info(
            "Looks like the helm deployment: %s", deployment.metadata.annotations
        )

        logger.info("Running helm instance tests")
        instance.test()

        logger.info("Checking helm instance status")
        status = instance.status()
        assert status.name == instance.name
        assert status.status == Status.DEPLOYED
        logger.info("--> Status: %s", status.description)

    # pylint: disable=broad-except
    except Exception as err:
        logger.error("helm operations failed: %s", err)
        raise err

    finally:
        logger.info("Stopping the helm release instance")
        instance.destroy()
