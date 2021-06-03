"""

PyTest NPods specific fixtures

Fixtures that are common only to these npods tests, so they are kept out of the outer
conftest file.

"""
import logging
import time
import json

import pytest

from mirantis.testing.metta.client import METTA_PLUGIN_TYPE_CLIENT
from mirantis.testing.metta.workload import METTA_PLUGIN_TYPE_WORKLOAD
from mirantis.testing.metta_mirantis.mke_client import METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID
from mirantis.testing.metta_kubernetes import METTA_PLUGIN_ID_KUBERNETES_CLIENT

logger = logging.getLogger('npods-test-conftest')
""" test-suite logger """

# ------ FIXTURES ------------------------------------------

# impossible to chain pytest fixtures without using the same names
# pylint: disable=redefined-outer-name
# unused argument is their to force dependency hierarchy
# pylint: disable=unused-argument


@pytest.fixture(scope="package")
def npods_config(environment):
    """ get the npods yaml config object """
    loaded = environment.config.load('npods')
    logger.info("Using npods config: %s", json.dumps(loaded.get(), indent=2))
    return loaded


@pytest.fixture(scope="package")
def mke(environment):
    """ get the mke client """
    try:
        return environment.fixtures.get_plugin(
            plugin_type=METTA_PLUGIN_TYPE_CLIENT, plugin_id=METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID)

    except KeyError as err:
        raise ValueError("No MKE client could be found. Is MKE installed?") from err


@pytest.fixture(scope="package")
def kubeapi(environment):
    """ get the kubeapi client """
    try:
        kubeapi_client = environment.fixtures.get_plugin(
            plugin_type=METTA_PLUGIN_TYPE_CLIENT, plugin_id=METTA_PLUGIN_ID_KUBERNETES_CLIENT)

        try:
            # helms wil fail if the kubeapi isn't ready
            logger.info("Waiting for kubernetes to be ready")
            kubeapi_client.ready_wait(45)

        except Exception as err:
            raise Exception(
                "Failed waiting for kubernetes to be ready") from err

        # @TODO remove4 this hardcoded sleep
        # this is only needed as helm sometimes fails without it
        logger.info("Extending wait period to fix an unknown helm issue. Waiting 30 seconds.")
        time.sleep(30)

        return kubeapi_client

    except KeyError as err:
        raise ValueError(
            "No Kubernetes client could be found. Is Kubernetes orchestration enabled??") from err


@pytest.fixture(scope="package")
def environment_up_unlocked(environment_up, mke, kubeapi):
    """ environment with pods/node unlocked using the mke client

    Use this to get the environment object, after the pods/node limit has
    been raised.

    This also performs an environment sanity test on clients.

    """

    try:
        data = mke.api_ucp_configtoml_get()
        data['cluster_config']['kubelet_max_pods'] = 2000
        mke.api_ucp_configtoml_put(data)

    except Exception as err:
        raise Exception("Failed when trying to raise the MKE limits for pods/node") from err

    # we didn't touch this but this is the return target
    return environment_up


@pytest.fixture(scope="module")
def npods(environment_up_unlocked, npods_config):
    """ create an instance of our helm workload plugin using fixtures from our env """
    npods_plugin = environment_up_unlocked.fixtures.get_plugin(
        plugin_type=METTA_PLUGIN_TYPE_WORKLOAD, instance_id='npods-workload')
    npods_instance = npods_plugin.create_instance(environment_up_unlocked.fixtures)
    """ npods helm workload defined in fixtures.yml, using fixtures from our environment """

    try:
        npods_instance.apply(wait=True)
    except Exception as err:
        raise RuntimeError(
            "Npods helm stack failed to initialize before running test") from err

    yield npods_instance

    npods_instance.destroy()
    return npods_instance


@pytest.fixture(scope="package")
def loki(environment_up_unlocked, npods_config):
    """ create an instance of the monitoring helm workload plugin using fixtures from our env """
    loki_plugin = environment_up_unlocked.fixtures.get_plugin(
        plugin_type=METTA_PLUGIN_TYPE_WORKLOAD, instance_id='loki-workload')
    loki_instance = loki_plugin.create_instance(environment_up_unlocked.fixtures)
    """ loki helm workload defined in fixtures.yml, using fixtures from our environment """

    try:
        if npods_config.get('monitoring.enable', default=True):
            # start the loki monitoring cluster
            logger.info("Starting loki monitoring stack")
            loki_instance.apply(wait=True)
        else:
            logger.debug(
                "Not starting the loki monitoring stack (because config said don't)")

    # pylint: disable=broad-except
    except BaseException:
        # this is not a blocking failure
        logger.error("Loki monitoring stack failed to start")

    return loki_instance
