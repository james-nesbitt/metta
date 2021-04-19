"""

Test that some clients work

"""

import logging
import pytest
import docker.models.containers

from mirantis.testing.metta.plugin import Type

logger = logging.getLogger("run chaos tests")


@pytest.fixture(scope="session")
def myapp_running(environment_up):
    """ get the myapp deployment running on the environment

    @REQUIRES : The environment must produce a kubernetes client fixture for the
        myapp kubernetes deployment workload plugin to use.
        In our case, the launchpad provisioner produces that plugin.

    """

    logger.info(
        "Starting a kubernetes workload in this environment, so that we can run litmus chaos against it.")

    sanity_kubernetes_deployment = environment_up.fixtures.get_plugin(type=Type.WORKLOAD, instance_id='myapp_deployment')
    instance = sanity_kubernetes_deployment.create_instance(environment_up.fixtures)
    deployment = instance.apply()

    assert deployment is not None
    logger.debug("RUNNING: myapp workload deployed: {}".format(deployment))

    yield instance

    # tear the deployment down
    status = instance.destroy()
    assert status is not None
    assert status.code is None
    logger.info("myapp deployment destroy status: {}".format(status))


@pytest.fixture(scope="session")
def litmuschaos_installed(environment_up):
    """ get the litmus chaos workload, installed on the environment

    @REQUIRES : The environment must produce a kubernetes client fixture for the
        myapp kubernetes deployment workload plugin to use.
        In our case, the launchpad provisioner produces that plugin.

    @NOTE this workload plugin is in early development and its requirements may
        change.

    """

    logger.info(
        "Preparing Litmus Chaos workload.")

    litmuchchaos_run = environment_up.fixtures.get_plugin(type=Type.WORKLOAD, instance_id='chaos_litmuschaos')
    instance = litmuchchaos_run.create_instance(environment_up.fixtures)
    applied = instance.prepare()

    # @TODOD test the applied

    yield instance

    # Tear down LitmusChaos
    instance.destroy()
    logger.info("Destroying LitmusChaos workload: {}".format(instance))


def test_01_install_chaos(environment_up, litmuschaos_installed):
    """ install LitmusChaos components """

    logger.info("We made it to here")
