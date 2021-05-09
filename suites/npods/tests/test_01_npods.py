"""

Test that we can apply nPods per node.

"""
import logging
import pytest
import time

from mirantis.testing.metta.plugin import Type
from mirantis.testing.metta_mirantis.mke_client import MKENodeState, METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID

logger = logging.getLogger('npods-test')
""" test-suite logger """

STABILITY_TEST_DURATION_MINUTES = 10
""" how many minutes we should run the test before we accept its stability """
STABILITY_TEST_PERIOD = 1
""" how frequently we should test stability """

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

    # we didn't touch this but this is the return target
    return environment_up


@pytest.fixture(scope="module")
def npods(environment_up_unlocked):
    """ create an instance of our helm workload plugin using fixtures from our env """
    npods_plugin = environment_up_unlocked.fixtures.get_plugin(
        type=Type.WORKLOAD, instance_id='npods-workload')
    npods = npods_plugin.create_instance(environment_up_unlocked.fixtures)
    """ npods helm workload defined in fixtures.yml, using fixtures from our environment """

    return npods


@pytest.fixture(scope="module")
def loki(environment_up):
    """ create an instance of the monitoring helm workload plugin using fixtures from our env """
    loki_plugin = environment_up.fixtures.get_plugin(
        type=Type.WORKLOAD, instance_id='loki-workload')
    loki = loki_plugin.create_instance(environment_up.fixtures)
    """ loki helm workload defined in fixtures.yml, using fixtures from our environment """

    return loki

# ------ TEST CASES ----------------------------------------


def test_01_initial_workload(environment_up_unlocked, loki, npods):
    """ testing on initial workload as defined in the fixture """

    loki.apply(wait=True)
    npods.apply(wait=True)
    _stability_test(environment_up_unlocked)


def test_02_1100_workload(environment_up_unlocked, npods):
    """ raise to 1100 pods and check stability """

    # Increas the workload replica count and try again
    npods.values["workloads"][0]["replicas"] = 550
    npods.values["workloads"][1]["replicas"] = 550
    npods.apply(wait=True)

    _stability_test(environment_up_unlocked)


def test_03_1400_workload(environment_up_unlocked, npods):
    """ raise to 1400 pods and check stability """

    # Increas the workload replica count and try again
    npods.values["workloads"][0]["replicas"] = 700
    npods.values["workloads"][1]["replicas"] = 700
    npods.apply(wait=True)

    _stability_test(environment_up_unlocked)


def test_04_1600_workload(environment_up_unlocked, npods):
    """ raise to 1600 pods and check stability """

    # Increas the workload replica count and try again
    npods.values["workloads"][0]["replicas"] = 800
    npods.values["workloads"][1]["replicas"] = 800
    npods.apply(wait=True)

    _stability_test(environment_up_unlocked)


def test_05_1800_workload(environment_up_unlocked, npods):
    """ raise to 1800 pods and check stability """

    # Increas the workload replica count and try again
    npods.values["workloads"][0]["replicas"] = 900
    npods.values["workloads"][1]["replicas"] = 900
    npods.apply(wait=True)

    _stability_test(environment_up_unlocked)


def test_06_2000_workload(environment_up_unlocked, npods):
    """ raise to 2000 pods and check stability """

    # Increas the workload replica count and try again
    npods.values["workloads"][0]["replicas"] = 1000
    npods.values["workloads"][1]["replicas"] = 1000
    npods.apply(wait=True)

    _stability_test(environment_up_unlocked)


def test_07_2200_workload(environment_up_unlocked, npods):
    """ raise to 2200 pods and check stability """

    # Increas the workload replica count and try again
    npods.values["workloads"][0]["replicas"] = 1100
    npods.values["workloads"][1]["replicas"] = 1100
    npods.apply(wait=True)

    _stability_test(environment_up_unlocked)


def test_08_2400_workload(environment_up_unlocked, npods):
    """ raise to 2400 pods and check stability """

    # Increas the workload replica count and try again
    npods.values["workloads"][0]["replicas"] = 1200
    npods.values["workloads"][1]["replicas"] = 1200
    npods.apply(wait=True)

    _stability_test(environment_up_unlocked)


def test_09_2600_workload(environment_up_unlocked, npods):
    """ raise to 2400 pods and check stability """

    # Increas the workload replica count and try again
    npods.values["workloads"][0]["replicas"] = 1300
    npods.values["workloads"][1]["replicas"] = 1300
    npods.apply(wait=True)

    _stability_test(environment_up_unlocked)


def test_10_2800_workload(environment_up_unlocked, npods):
    """ raise to 2400 pods and check stability """

    # Increas the workload replica count and try again
    npods.values["workloads"][0]["replicas"] = 1400
    npods.values["workloads"][1]["replicas"] = 1400
    npods.apply(wait=True)

    _stability_test(environment_up_unlocked)


def test_99_teardown(environment_up_unlocked, npods):
    """ tear down the namespace we ran in """

    npods.destroy()

# ------ UTILITY -------------------------------------------


def _stability_test(environment):
    """ Run a stability test on the cluster """

    mke = environment.fixtures.get_plugin(
        type=Type.CLIENT, plugin_id=METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID)
    """ The mke client api (again) """

    timeout = time.time() + 60 * STABILITY_TEST_DURATION_MINUTES
    index = 1
    while True:
        if time.time() > timeout:
            break

        mke_nodes = mke.api_nodes()
        """ list of nodes for the mke client """
        for node in mke_nodes:
            assert MKENodeState.READY.match(
                node['Status']['State']), "MKE NODE {} was not in a READY state: {}".format(
                node['ID'], node['Status'])

        logger.info("{} [{}]: all is well".format(index, time.time()))
        time.sleep(60 * STABILITY_TEST_PERIOD)
        index += 1
