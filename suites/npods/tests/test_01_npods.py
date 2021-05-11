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

STABILITY_TEST_DURATION_MINUTES = 2
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

    #start the loki monitoring cluster
    loki.apply(wait=True)

    return loki

# ------ TEST CASES ----------------------------------------


def test_01_initial_workload(environment_up_unlocked, loki, npods):
    """ testing stability on initial workload as defined in the fixture """

    # start the initial cluster resources.
    npods.apply(wait=True)

    # run the first run of stability tests.
    _stability_test(environment_up_unlocked,
                    logger.getChild('npods-initial-sanity'))


@pytest.mark.skip(reason="Always passes with current system")
def test_02_1100_workload(environment_up_unlocked, npods):
    """ raise to 1100 pods and check stability """

    # Increase the workload replica count and test again
    npods.values["workloads"][0]["replicas"] = 550
    npods.values["workloads"][1]["replicas"] = 550
    npods.apply(wait=True)

    _stability_test(environment_up_unlocked, logger.getChild('npods-1100'))


@pytest.mark.skip(reason="Always passes with current system")
def test_03_1400_workload(environment_up_unlocked, npods):
    """ raise to 1400 pods and check stability """

    # Increase the workload replica count and test again
    npods.values["workloads"][0]["replicas"] = 700
    npods.values["workloads"][1]["replicas"] = 700
    npods.apply(wait=True)

    _stability_test(environment_up_unlocked, logger.getChild('npods-1400'))


@pytest.mark.skip(reason="Always passes with current system")
def test_04_1600_workload(environment_up_unlocked, npods):
    """ raise to 1600 pods and check stability """

    # Increase the workload replica count and test again
    npods.values["workloads"][0]["replicas"] = 800
    npods.values["workloads"][1]["replicas"] = 800
    npods.apply(wait=True)

    _stability_test(environment_up_unlocked, logger.getChild('npods-1600'))


@pytest.mark.skip(reason="Always passes with current system")
def test_05_1800_workload(environment_up_unlocked, npods):
    """ raise to 1800 pods and check stability """

    # Increase the workload replica count and test again
    npods.values["triggers"].append({"name":"1800", "thread":100})
    npods.values["workloads"][0]["replicas"] = 900
    npods.values["workloads"][1]["replicas"] = 900
    npods.apply(wait=True)

    _stability_test(environment_up_unlocked, logger.getChild('npods-1800'))


def test_06_2000_workload(environment_up_unlocked, npods):
    """ raise to 2000 pods and check stability """

    # Increase the workload replica count and test again
    npods.values["triggers"].append({"name":"2000", "thread":100})
    npods.values["workloads"][0]["replicas"] = 1000
    npods.values["workloads"][1]["replicas"] = 1000
    npods.apply(wait=True)

    _stability_test(environment_up_unlocked, logger.getChild('npods-2000'))


def test_07_2200_workload(environment_up_unlocked, npods):
    """ raise to 2200 pods and check stability """

    # Increase the workload replica count and test again
    npods.values["workloads"][0]["replicas"] = 1100
    npods.values["workloads"][1]["replicas"] = 1100
    npods.apply(wait=True)

    _stability_test(environment_up_unlocked, logger.getChild('npods-2200'))


def test_08_2400_workload(environment_up_unlocked, npods):
    """ raise to 2400 pods and check stability """

    # Increase the workload replica count and test again
    npods.values["workloads"][0]["replicas"] = 1200
    npods.values["workloads"][1]["replicas"] = 1200
    npods.apply(wait=True)

    _stability_test(environment_up_unlocked, logger.getChild('npods-2400'))


def test_09_2600_workload(environment_up_unlocked, npods):
    """ raise to 2600 pods and check stability """

    # Increase the workload replica count and test again
    npods.values["workloads"][0]["replicas"] = 1300
    npods.values["workloads"][1]["replicas"] = 1300
    npods.apply(wait=True)

    _stability_test(environment_up_unlocked, logger.getChild('npods-2600'))


def test_10_2800_workload(environment_up_unlocked, npods):
    """ raise to 2800 pods and check stability """

    # Increase the workload replica count and test again
    npods.values["workloads"][0]["replicas"] = 1400
    npods.values["workloads"][1]["replicas"] = 1400
    npods.apply(wait=True)

    _stability_test(environment_up_unlocked, logger.getChild('npods-2800'))


def test_11_3000_workload(environment_up_unlocked, npods):
    """ raise to 3000 pods and check stability """

    # Increase the workload replica count and test again
    npods.values["workloads"][0]["replicas"] = 1500
    npods.values["workloads"][1]["replicas"] = 1500
    npods.apply(wait=True)

    _stability_test(environment_up_unlocked, logger.getChild('npods-3000'))


@pytest.mark.skip(reason="Way too many for the current system")
def test_12_3200_workload(environment_up_unlocked, npods):
    """ raise to 3200 pods and check stability """

    # Increase the workload replica count and test again
    npods.values["workloads"][0]["replicas"] = 1600
    npods.values["workloads"][1]["replicas"] = 1600
    npods.apply(wait=True)

    _stability_test(environment_up_unlocked, logger.getChild('npods-3200'))


@pytest.mark.skip(reason="Way too many for the current system")
def test_13_3400_workload(environment_up_unlocked, npods):
    """ raise to 3400 pods and check stability """

    # Increase the workload replica count and test again
    npods.values["workloads"][0]["replicas"] = 1700
    npods.values["workloads"][1]["replicas"] = 1700
    npods.apply(wait=True)

    _stability_test(environment_up_unlocked, logger.getChild('npods-3400'))


@pytest.mark.skip(reason="Way too many for the current system")
def test_14_3600_workload(environment_up_unlocked, npods):
    """ raise to 3600 pods and check stability """

    # Increase the workload replica count and test again
    npods.values["workloads"][0]["replicas"] = 1800
    npods.values["workloads"][1]["replicas"] = 1800
    npods.apply(wait=True)

    _stability_test(environment_up_unlocked, logger.getChild('npods-3600'))


@pytest.mark.skip(reason="Way too many for the current system")
def test_15_3800_workload(environment_up_unlocked, npods):
    """ raise to 3800 pods and check stability """

    # Increase the workload replica count and test again
    npods.values["workloads"][0]["replicas"] = 1900
    npods.values["workloads"][1]["replicas"] = 1900
    npods.apply(wait=True)

    _stability_test(environment_up_unlocked, logger.getChild('npods-3800'))


@pytest.mark.skip(reason="Way too many for the current system")
def test_16_4000_workload(environment_up_unlocked, npods):
    """ raise to 4000 pods and check stability """

    # Increase the workload replica count and test again
    npods.values["workloads"][0]["replicas"] = 2000
    npods.values["workloads"][1]["replicas"] = 2000
    npods.apply(wait=True)

    _stability_test(environment_up_unlocked, logger.getChild('npods-4000'))


@pytest.mark.skip(reason="Way too many for the current system")
def test_17_4200_workload(environment_up_unlocked, npods):
    """ raise to 4200 pods and check stability """

    # Increase the workload replica count and test again
    npods.values["workloads"][0]["replicas"] = 2100
    npods.values["workloads"][1]["replicas"] = 2100
    npods.apply(wait=True)

    _stability_test(environment_up_unlocked, logger.getChild('npods-4200'))


def test_99_teardown(environment_up_unlocked, npods, loki):
    """ tear down the namespace we ran in """

    # remove the npods resources, so that you can run the test again
    # without anythin left in place.
    npods.destroy()

    # We keep the loki chart installed so that you can use it for
    # analysis after the test run.
    # loki.destroy()

# ------ UTILITY -------------------------------------------


def _stability_test(environment, logger=logger):
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
        elif unhealthy_count < 3:
            logger.warn(
                "{} [{}]: Some nodes are unhappy".format(
                    index, time.time()))
        else:
            logger.error(
                "{} [{}]: Cluster is unhealthy".format(
                    index, time.time()))
            raise Exception("Cluster is unhealthy, so this test will stop")

        time.sleep(60 * STABILITY_TEST_PERIOD)
        index += 1
