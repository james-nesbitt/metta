"""

Test that we can apply nPods per node.

"""
import logging
import pytest
import time
import json

from mirantis.testing.metta.plugin import Type
from mirantis.testing.metta_mirantis.mke_client import MKENodeState, METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID
from mirantis.testing.metta_kubernetes import METTA_PLUGIN_ID_KUBERNETES_CLIENT

logger = logging.getLogger('npods-test')
""" test-suite logger """

STABILITY_TEST_DURATION_MINUTES = 1 * 60
""" how long we should run the test before we accept its stability (seconds) """
STABILITY_TEST_PERIOD = 30
""" how frequently we should test stability (seconds) """


# ------ FIXTURES ------------------------------------------


@pytest.fixture(scope="module")
def environment_up_unlocked(environment_up):
    """ environment with pods/node unlocked using the mke client

    Use this to get the environment object, after the pods/node limit has
    been raised.

    This also performs an environment sanity test on clients.

    """

    try:
        mke = environment_up.fixtures.get_plugin(
            type=Type.CLIENT, plugin_id=METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID)

    except KeyError as e:
        raise ValueError(
            "No MKE client could be found. Is MKE installed?") from e

    try:
        data = mke.api_ucp_configtoml_get()
        data['cluster_config']['kubelet_max_pods'] = 2000
        mke.api_ucp_configtoml_put(data)

    except Exception as e:
        raise Exception(
            "Failed when trying to raise the MKE limits for pods/node") from e

    try:
        kubeapi = environment_up.fixtures.get_plugin(
        type=Type.CLIENT, plugin_id=METTA_PLUGIN_ID_KUBERNETES_CLIENT)

    except KeyError as e:
        raise ValueError("No Kubernetes client could be found. Is Kubernetes orchestration enabled??") from e

    try:
        # helms wil fail if the kube
        logger.info("Waiting for kubernetes to be ready")
        kubeapi.ready_wait(30)

    except Exception as e:
        raise Exception(
            "Failed waiting for kubernetes to be ready") from e

    # I tried a number of ways to get around this, but I kept running into errors
    # where helm would start, and then fail with a message:
    #    Error: an error on the server ("unknown") has prevented the request from succeeding (get services npods-relay-initial)
    # @TODO figure out why this is needed.
    # logger.info('Giving MKE some time to settle, which makes helm much more stable')
    # time.sleep(10)

    # we didn't touch this but this is the return target
    return environment_up


@pytest.fixture(scope="module")
def npods(environment_up_unlocked):
    """ create an instance of our helm workload plugin using fixtures from our env """
    npods_plugin = environment_up_unlocked.fixtures.get_plugin(
        type=Type.WORKLOAD, instance_id='npods-workload')
    npods = npods_plugin.create_instance(environment_up_unlocked.fixtures)
    """ npods helm workload defined in fixtures.yml, using fixtures from our environment """

    try:
        npods.apply(wait=True)
    except Exception as e:
        logger.error("Npods Helm error.\nValues: {}\n kubeconfig:{}".format())

    yield npods

    npods.destroy()
    return npods

@pytest.fixture(scope="module")
def loki(environment_up):
    """ create an instance of the monitoring helm workload plugin using fixtures from our env """
    loki_plugin = environment_up.fixtures.get_plugin(
        type=Type.WORKLOAD, instance_id='loki-workload')
    loki = loki_plugin.create_instance(environment_up.fixtures)
    """ loki helm workload defined in fixtures.yml, using fixtures from our environment """

    #start the loki monitoring cluster
    loki.apply(wait=True)

    return loki

# ------ UTILITY -------------------------------------------

total = 0
""" track how many pods have we scaled up to """

def _create_scale_and_test_function(replicas: int, triggers: int):

    def _scale_and_test(environment_up_unlocked, npods):
        """ Scale up the workloads """
        global total

        new_total = total + replicas
        name = "{}".format(new_total)

        ## Add a workload to the helm chart
        npods.values["workloads"].append({
            'name': name,
            'replicas': replicas,
            'image': 'msr.ci.mirantis.com/jnesbitt/n-pods-app:0.18',
            'sleep': '10ms',
            'cpu': '300',
            'ram': '8192',
            'threads': triggers
        })
        logger.debug(json.dumps(npods.values["workloads"], indent=2))
        npods.apply(wait=True)

        # store the new total value after helm has been applied, and before we
        # test stability, in case the stability test throws an exception
        total = new_total

        # stability test communicates by raising exceptions
        _stability_test(environment=environment_up_unlocked, logger=logger.getChild(name))

    return _scale_and_test


def _stability_test(environment, logger=logger):
    """ Run a stability test on the cluster

    Returns:
    --------

    Nothing

    Raise:
    ------

    Raises an exception if more than 1 node is unhealthy

    """

    mke = environment.fixtures.get_plugin(
        type=Type.CLIENT, plugin_id=METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID)
    """ The mke client api (again) """

    timeout = time.time() + STABILITY_TEST_DURATION_MINUTES
    index = 1
    while True:
        if time.time() > timeout:
            break

        mke_nodes = mke.api_nodes()
        """ list of nodes for the mke client """
        unhealthy_count = 0
        for node in mke_nodes:
            try:
                assert MKENodeState.READY.match(
                    node['Status']['State']), "MKE NODE {} was not in a READY state: {}".format(
                    node['ID'], node['Status'])
            except Exception as e:
                unhealthy_count += 1
                logger.warn("{}".format(e))

        if unhealthy_count == 0:
            logger.info("{} [{}]: all is well".format(index, time.time()))
        elif unhealthy_count < 2:
            logger.warning(
                "{} [{}]: Some nodes are unhappy".format(
                    index, time.time()))
        else:
            logger.error(
                "{} [{}]: Cluster is unhealthy".format(
                    index, time.time()))
            raise Exception("Cluster is unhealthy, so this test will stop")

        time.sleep(STABILITY_TEST_PERIOD)
        index += 1

# ------ TEST CASES ---------------------------------------


test_01_500 = _create_scale_and_test_function(500,500)
""" Initial scale up to 500 pods """
test_02_1000 = _create_scale_and_test_function(500,500)
""" Scale up to 1000 pods """
test_03_test = _create_scale_and_test_function(500,500)
""" Scale up to 1500 pods """
test_04_test = _create_scale_and_test_function(500,500)
""" Scale up to 2000 pods """
test_05_test = _create_scale_and_test_function(100,100)
""" Scale up to 2100 pods """
test_06_test = _create_scale_and_test_function(100,100)
""" Scale up to 2200 pods """
test_07_test = _create_scale_and_test_function(100,100)
""" Scale up to 2300 pods """
test_08_test = _create_scale_and_test_function(100,100)
""" Scale up to 2400 pods """
test_09_test = _create_scale_and_test_function(100,100)
""" Scale up to 2500 pods """
