"""

Test that the teraform provisioner can bring up a local cluster.

"""

import logging

from mirantis.testing.metta import Environment
from mirantis.testing.metta_terraform.provisioner import TerraformProvisionerPlugin
from mirantis.testing.metta.output import METTA_PLUGIN_INTERFACE_ROLE_OUTPUT

logger = logging.getLogger("test_cluster")


# pylint: disable=unused-argument
def test_terraform_upped(environment_up: Environment):
    """Test that the terraform provisioner was able to bring up the cluster."""


# pylint: disable=unused-argument
def test_terraform_output(
    environment_up: Environment, terraform_provisioner: TerraformProvisionerPlugin
):
    """Test that the terraform provisioner created terraform outputs."""

    output_fixtures = terraform_provisioner.fixtures.filter(
        interfaces=[METTA_PLUGIN_INTERFACE_ROLE_OUTPUT]
    )

    assert len(output_fixtures) > 0, "Terraform provisioner did not produce any output"
