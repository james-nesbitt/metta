"""

Test that we are able to provision the system and interact
with cluster elements.

Here our test harness uses the provisioner plugins to create a running system
and then interacts in the system in a few ways.

Here we:

1. Use the provisioners to start the running system
2. use a few of the provisioner clients to test MKE and MSR health
3. use a workload plugin/fixture to run a workload on the cluster and ensure
   that it is running correctly
4. tear the system down
5. test that it was torn down properly.

@NOTE this approach includes the building of the system as a test function,
    which is usefull in the sanity scenario, but not a normal way to test
    a cluster.  Normally you want a fixture which creates the running cluster
    outside of your test functions so that you can benchmark without including
    the cluster setup as a part of a test-case.
    Check the other suites for such an approach.

"""
import logging
import pytest

from mirantis.testing.metta.plugin import Type
from mirantis.testing.metta_docker import METTA_PLUGIN_ID_DOCKER_CLIENT
from mirantis.testing.metta_kubernetes import METTA_PLUGIN_ID_KUBERNETES_CLIENT
from mirantis.testing.metta_launchpad import METTA_LAUNCHPAD_EXEC_CLIENT_PLUGIN_ID
from mirantis.testing.metta_mirantis.msr_client import MSRReplicaHealth, METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID
from mirantis.testing.metta_mirantis.mke_client import MKENodeState, METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID

logger = logging.getLogger('sanity:Provisioning')


def test_01_environment_prepare(environment):
    """ get the environment but prepare the provisioners before returning

    This is preferable to the raw provisioner in cases where you want a running
    cluster so that the cluster startup cost does not get reflected in the
    first test case which uses the fixture.  Also it can tear itself down

    You can still use the provsioners to update the resources if the provisioner
    plugins can handle it.
    """

    provisioner = environment.fixtures.get_plugin(type=Type.PROVISIONER)
    """ Combo provisioner wrapper for terraform/ansible/launchpad """

    # We will use this config to make decisions about what we need to create
    # and destroy for this environment up.
    conf = environment.config.load("config")
    """ somewhat equivalent to reading ./config/config.yml """

    if conf.get("alreadyrunning", default=False):
        logger.info(
            "test infrastructure is aready in place, and does not need to be provisioned.")
    else:
        try:
            logger.info("Preparing the testing cluster using the provisioner")
            provisioner.prepare()
        except Exception as e:
            logger.error("Provisioner failed to init: %s", e)
            raise e


def test_02_environment_up(environment):
    """ get the environment but start the provisioners before returning

    This is preferable to the raw provisioner in cases where you want a running
    cluster so that the cluster startup cost does not get reflected in the
    first test case which uses the fixture.  Also it can tear itself down

    You can still use the provsioners to update the resources if the provisioner
    plugins can handle it.
    """

    provisioner = environment.fixtures.get_plugin(type=Type.PROVISIONER)
    """ Combo provisioner wrapper for terraform/ansible/launchpad """

    # We will use this config to make decisions about what we need to create
    # and destroy for this environment up.
    conf = environment.config.load("config")
    """ somewhat equivalent to reading ./config/config.yml """

    if conf.get("alreadyrunning", default=False):
        logger.info(
            "test infrastructure is aready in place, and does not need to be provisioned.")
    else:
        try:
            logger.info(
                "Starting up the testing cluster using the provisioner")

            provisioner.apply()
        except Exception as e:
            logger.error("Provisioner failed to start: %s", e)
            raise e


def test_03_terraform_sanity(environment):
    """ test that the terraform provisioner is happy, and that it has our expected outputs """

    launchpad = environment.fixtures.get_plugin(
        type=Type.PROVISIONER, instance_id='launchpad')


def test_04_launchpad_sanity(environment):
    """ test that the launchpad provisioner is happy, and that it produces our expected clients """

    launchpad = environment.fixtures.get_plugin(
        type=Type.PROVISIONER, instance_id='launchpad')


def test_05_expected_clients(environment):
    """ test that the environment gave us some expected clients """

    logger.info("Getting docker client")
    docker_client = environment.fixtures.get_plugin(type=Type.CLIENT,
                                                    plugin_id=METTA_PLUGIN_ID_DOCKER_CLIENT)

    logger.info("Getting exec client")
    exec_client = environment.fixtures.get_plugin(type=Type.CLIENT,
                                                  plugin_id=METTA_LAUNCHPAD_EXEC_CLIENT_PLUGIN_ID)

    logger.info("Getting K8s client")
    kubectl_client = environment.fixtures.get_plugin(type=Type.CLIENT,
                                                     plugin_id=METTA_PLUGIN_ID_KUBERNETES_CLIENT)


container_index = 0
""" Use a global container index for error reporting on container creation """


def test_06_docker_run_workload(environment, benchmark):
    """ test that we can run a docker run workload """

    # we have a docker run workload fixture called "sanity_docker_run"
    sanity_docker_run = environment.fixtures.get_plugin(type=Type.WORKLOAD,
                                                        instance_id='sanity_docker_run')
    """ workload plugin """
    def container_run():
        global container_index
        container_index += 1
        try:
            docker_run_instance = sanity_docker_run.create_instance(
                environment.fixtures)
            run_output = docker_run_instance.apply()
            assert 'Hello from Docker' in run_output.decode("utf-8")
        except Exception as e:
            raise RuntimeError(
                'Docker run [{}] failed: {}'.format(
                    container_index, e)) from e

    benchmark(container_run)


def test_07_mke_api_info(environment):
    """ did we get a good mke client """

    # get the mke client.
    # We could get this from the launchpad provisioner if we were worried about
    # which mke client plugin instance we receive,  however there is only one
    # in this case.
    mke_client = environment.fixtures.get_plugin(
        type=Type.CLIENT, plugin_id=METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID)

    info = mke_client.api_info()
    logger.info("MKE Cluster ID: {}".format(info['ID']))
    logger.info("--> Warnings : {}".format(info['Warnings']))


def test_08_mke_nodes_health(environment):
    """ did we get a good mke client """

    mke_client = environment.fixtures.get_plugin(
        type=Type.CLIENT, plugin_id=METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID)

    nodes = mke_client.api_nodes()

    for node in nodes:
        assert MKENodeState.READY.match(
            node['Status']['State']), "MKE NODE {} was not in a READY state: {}".format(
            node['ID'], node['Status'])


def test_09_mke_swarminfo_health(environment):
    """ did we get a good mke client """

    mke_client = environment.fixtures.get_plugin(
        type=Type.CLIENT, plugin_id=METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID)

    info = mke_client.api_info()

    if 'Swarm' in info:
        swarm_info = info['Swarm']

        assert swarm_info['Nodes'] > 0, "MKE reports no nodes in the cluster"


def test_10_msr_client(environment):
    """ did we get a good msr client """

    # get the mke client.
    # We could get this from the launchpad provisioner if we were worried about
    # which mke client plugin instance we receive,  however there is only one
    # in this case.
    msr_client = environment.fixtures.get_plugin(
        type=Type.CLIENT, plugin_id=METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID)


def test_11_msr_root_health(environment):
    """ test the the node specific ping and health checks don't fail """
    msr_client = environment.fixtures.get_plugin(
        type=Type.CLIENT, plugin_id=METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID)

    for i in range(0, msr_client.host_count()):
        assert msr_client.api_ping(node=i)
        assert msr_client.api_health(node=i)["Healthy"]

        print("{}: NGINX: {}".format(i, msr_client.api_nginx_status(node=i)))


def test_12_msr_replica_health(environment):
    """ test that we can access node information """

    msr_client = environment.fixtures.get_plugin(
        type=Type.CLIENT, plugin_id=METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID)

    status = msr_client.api_status()
    for replica_id, replica_health in status['replica_health'].items():
        assert MSRReplicaHealth.OK.match(
            replica_health), "Replica [{}] did is not READY : {}".format(replica_id, replica_health)


def test_13_msr_alerts(environment):
    """ check that we can get alerts """

    msr_client = environment.fixtures.get_plugin(
        type=Type.CLIENT, plugin_id=METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID)

    alerts = msr_client.api_alerts()

    if len(alerts) > 0:

        for alert in alerts:
            logger.warning(
                "{}: {} [{}]".format(
                    alert['id'],
                    alert['message'],
                    alert['url'] if 'url' in alert else 'no-url'))


def test_14_environment_down(environment):
    """ tear down the environment """

    provisioner = environment.fixtures.get_plugin(type=Type.PROVISIONER)
    """ Combo provisioner wrapper for terraform/ansible/launchpad """

    # We will use this config to make decisions about what we need to create
    # and destroy for this environment up.
    conf = environment.config.load("config")
    """ somewhat equivalent to reading ./config/config.yml """

    if conf.get("keeponfinish", default=False):
        logger.info("Leaving test infrastructure in place on shutdown")
    else:
        try:
            logger.info(
                "Stopping the test cluster using the provisioner as directed by config")
            provisioner.destroy()
        except Exception as e:
            logger.error("Provisioner failed to stop: %s", e)
            raise e

    return environment


def test_15_torn_down(environment):
    """ test that we have a torn down environment

    @NOTE I am not sure how to confirm that we are down.  Perhaps we can ask for Terraform state?

    """

    pass
