"""

Test that we are able to provision the system and interact
with cluster elements.

"""
import logging
import pytest

from mirantis.testing.metta.plugin import Type
from mirantis.testing.metta_docker import METTA_PLUGIN_ID_DOCKER_CLIENT
from mirantis.testing.metta_kubernetes import METTA_PLUGIN_ID_KUBERNETES_CLIENT
from mirantis.testing.metta_launchpad import METTA_LAUNCHPAD_EXEC_CLIENT_PLUGIN_ID

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

    if conf.get("alreadyrunning", exception_if_missing=False):
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

    if conf.get("alreadyrunning", exception_if_missing=False):
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


def test_07_environment_down(environment):
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

    if conf.get("keeponfinish", exception_if_missing=False):
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


def test_08_torn_down(environment):
    """ test that we have a torn down environment

    @NOTE I am not sure how to confirm that we are down.  Perhaps we can ask for Terraform state?

    """

    pass
