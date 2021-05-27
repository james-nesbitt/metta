"""

Test that the teraform provisioner  can bring up a local cluster

"""

import logging

from mirantis.testing.metta import Environment
from mirantis.testing.metta_terraform.provisioner import TerraformProvisionerPlugin
from mirantis.testing.metta.output import METTA_PLUGIN_TYPE_OUTPUT

logger = logging.getLogger("test_clients")


# pylint: disable=unused-argument
def test_terraform_upped(environment_up: Environment):
    """ test that the terraform provisioner was able to bring up the cluster """


# pylint: disable=unused-argument
def test_terraform_output(environment_up: Environment,
                          terraform_provisioner: TerraformProvisionerPlugin):
    """ test that the terraform provisioner was able to bring up the cluster """

    output_fixtures = terraform_provisioner.fixtures.filter(plugin_type=METTA_PLUGIN_TYPE_OUTPUT)

    assert len(output_fixtures) > 0, "Terraform provisioner did not produce any output"
