"""

A single low-impact sanity test suite

Test that we have loadable configuration, and no issues bootstrapping. Here
we are testing Metta and your metta configuration, not actually testing your
cluster.

None of these tests expect your cluster to be provisioned.

What we are testing here is that the configuration used resulted in the expected
System of provisioner fixtures/plugins, and that those fixtures meet their
sanity markers.

"""
import logging


from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.provisioner import METTA_PLUGIN_INTERFACE_ROLE_PROVISIONER
from mirantis.testing.metta.workload import METTA_PLUGIN_INTERFACE_ROLE_WORKLOAD

# import for asserting provisioner plugin ids and classes
from mirantis.testing.metta_common import METTA_PLUGIN_ID_PROVISIONER_COMBO
from mirantis.testing.metta_common.combo_provisioner import ComboProvisionerPlugin
from mirantis.testing.metta_launchpad import METTA_LAUNCHPAD_PROVISIONER_PLUGIN_ID
from mirantis.testing.metta_launchpad.provisioner import LaunchpadProvisionerPlugin
from mirantis.testing.metta_terraform import METTA_TERRAFORM_PROVISIONER_PLUGIN_ID
from mirantis.testing.metta_terraform import TerraformProvisionerPlugin

# import for asserting workload plugin id and class
from mirantis.testing.metta_docker import METTA_PLUGIN_ID_DOCKER_RUN_WORKLOAD
from mirantis.testing.metta_docker.run_workload import DockerPyRunWorkloadPlugin

logger = logging.getLogger("Sanity::metta-sanity")


def test_environment_sanity(environment: Environment):
    """did we get the epxected environment"""
    assert environment.name == "sanity"


def test_provisioners(environment: Environment):
    """did we get the epxected environment provisioner fixtures"""
    logger.info("Getting provisioners")

    # we load some provisioners by instance id, which should match what you
    # see in `metta config get fixtures`. For each we retrieve the fixture
    # to compare metadata, and the plugin to make sure it is what we expect.

    # @NOTE all "instance_id" values must match the config/fixtures.yml keys

    combo_fixture = environment.fixtures.get(
        interfaces=[METTA_PLUGIN_INTERFACE_ROLE_PROVISIONER], instance_id="combo"
    )
    combo = combo_fixture.plugin
    """ the combo provisioner is a special provisioner aggregator """

    assert combo_fixture.plugin_id == METTA_PLUGIN_ID_PROVISIONER_COMBO
    assert combo_fixture.instance_id == "combo"
    assert isinstance(combo, ComboProvisionerPlugin)

    # Also test that the combo provisioner is the default one
    assert (
        environment.fixtures.get(
            interfaces=[METTA_PLUGIN_INTERFACE_ROLE_PROVISIONER]
        ).instance_id
        == "combo"
    )

    launchpad_fixture = environment.fixtures.get(
        instance_id="launchpad", interfaces=[METTA_PLUGIN_INTERFACE_ROLE_PROVISIONER]
    )
    launchpad = launchpad_fixture.plugin

    assert launchpad_fixture.plugin_id == METTA_LAUNCHPAD_PROVISIONER_PLUGIN_ID
    assert launchpad_fixture.instance_id == "launchpad"
    assert isinstance(launchpad, LaunchpadProvisionerPlugin)

    terraform_fixture = environment.fixtures.get(
        instance_id="terraform", interfaces=[METTA_PLUGIN_INTERFACE_ROLE_PROVISIONER]
    )
    terraform = terraform_fixture.plugin

    assert terraform_fixture.plugin_id == METTA_TERRAFORM_PROVISIONER_PLUGIN_ID
    assert terraform_fixture.instance_id == "terraform"
    assert isinstance(terraform, TerraformProvisionerPlugin)


def test_workload(environment: Environment):
    """did we get the epxected environment workload fixtures"""

    logger.info("Getting workloads")

    # we load some worklaods by instance id, which should match what you
    # see in `metta config get fixtures`. Then we confirm their plugin types.

    sanity_docker_run_fixture = environment.fixtures.get(
        instance_id="sanity_docker_run",
    )
    sanity_docker_run = sanity_docker_run_fixture.plugin

    assert sanity_docker_run_fixture.plugin_id == METTA_PLUGIN_ID_DOCKER_RUN_WORKLOAD
    assert isinstance(sanity_docker_run, DockerPyRunWorkloadPlugin)
