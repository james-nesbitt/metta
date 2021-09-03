"""

Metta client plugin for terraform.

The metta client plugin is a client which can run terraform using
an assigned chart.

"""
import logging
from typing import Dict, Any
import os
import json

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.fixture import Fixtures
from mirantis.testing.metta.output import METTA_PLUGIN_INTERFACE_ROLE_OUTPUT
from mirantis.testing.metta_common import (
    METTA_PLUGIN_ID_OUTPUT_DICT,
    METTA_PLUGIN_ID_OUTPUT_TEXT,
)

from .terraform import TerraformClient


logger = logging.getLogger("metta_terraform:client")


METTA_TERRAFORM_CLIENT_PLUGIN_ID = "metta_terraform_client"
""" Terraform provisioner plugin id """


class TerraformClientPlugin:
    """Metta terraform client."""

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        environment: Environment,
        instance_id: str,
        chart_path: str,
        state_path: str,
        tfvars: Dict[str, Any],
        tfvars_path: str,
    ):
        """Initial client configuration."""
        self._environment: Environment = environment
        """ Environemnt in which this plugin exists """
        self._instance_id: str = instance_id
        """ Unique id for this plugin instance """

        self.tfvars: Dict[str, Any] = tfvars
        """Terraform vars to pass to TF as a tfvars file."""
        self._tfvars_path: str = os.path.realpath(tfvars_path)
        """Path to write for the tfvars file."""

        self._tf_handler = TerraformClient(
            working_dir=os.path.realpath(chart_path),
            state_path=os.path.realpath(state_path),
            tfvars_path=os.path.realpath(tfvars_path),
        )
        """Terraform handler which actually runs terraform commands."""

        self.fixtures = Fixtures()
        """All fixtures added to this plugin, which are primarily TF output plugins."""

        # if the cluster is already provisioned then we can get outputs from it
        try:
            self.make_fixtures()
        # pylint: disable=broad-except
        except Exception:
            pass

    # deep argument is an info() standard across plugins
    # pylint: disable=unused-argument
    def info(self, deep: bool = False):
        """Get info about the client plugin.

        Returns:
        --------
        Dict of keyed introspective information about the plugin.

        """
        info = {
            "config": {
                "tfvars": self.tfvars,
                "tfvars_path": self._tfvars_path,
            },
            "client": self._tf_handler.info(deep=deep),
        }

        return info

    def state(self):
        """Return the terraform state contents."""
        return self._tf_handler.state()

    def init(self):
        """Run terraform init."""
        self._tf_handler.init()

    def apply(self, lock: bool = True):
        """Apply a terraform plan."""
        self._make_tfvars_file()
        self._tf_handler.apply(lock=lock)
        self.make_fixtures()

    def destroy(self, lock: bool = True):
        """Apply a terraform plan."""
        self._tf_handler.destroy(lock=lock)
        self._rm_tfvars_file()

    def test(self):
        """Apply a terraform plan."""
        self._make_tfvars_file()
        return self._tf_handler.test()

    def plan(self):
        """Check a terraform plan."""
        self._make_tfvars_file()
        return self._tf_handler.plan()

    def output(self, name: str = ""):
        """Retrieve terraform outputs.

        Run the terraform output command, to retrieve outputs.
        Outputs are returned always as json as it is the only way to machine
        parse outputs properly.

        Returns:
        --------
        If you provided a name, then a single output is returned, otherwise a
        dict of outputs is returned.

        """
        return self._tf_handler.output(name=name)

    def _make_tfvars_file(self):
        """Write the vars file."""
        os.makedirs(os.path.dirname(self._tfvars_path), exist_ok=True)
        with open(self._tfvars_path, "w", encoding="utf8") as var_file:
            json.dump(self.tfvars, var_file, sort_keys=True, indent=4)

    def _rm_tfvars_file(self):
        """Remove any created vars file."""
        tfvars_path = self._tfvars_path
        if os.path.isfile(tfvars_path):
            os.remove(tfvars_path)

    def make_fixtures(self):
        """Retrieve an output from terraform.

        For other METTA plugins we can just load configuration, and creating
        output plugin instances from various value in config.

        We do that here, but  we also want to check of any outputs exported by
        the terraform root module, which we get using the tf client.

        If we find a root module output without a matching config output
        defintition then we make some assumptions about plugin type and add it
        to the list. We make some simple investigation into output plugin types
        and pick either the contrib.common.dict or contrib.common.text plugins.

        If we find a root module output that matches an output that was
        declared in config then we use that.  This allows config to define a
        plugin_id which will then be populated automatically.  If you know what
        type of data you are expecting from a particular tf output then you can
        prepare and config for it to do things like setting default values.

        Priorities can be used in the config.

        """
        # now we ask TF what output it nows about and merge together those as
        # new output plugins.
        # tf.outputs() produces a list of (sensitive:bool, type: [str,  object,
        # value:Any])
        for output_key, output_struct in self.output().items():
            # Here is the kind of info we can get out of terraform
            # output_sensitive = bool(output_struct['sensitive'])
            # """ Whether or not the output contains sensitive data """
            output_type = output_struct["type"][0]
            # output_spec = output_struct['type'][1]
            # """ A structured spec for the type """
            output_value = output_struct["value"]

            # see if we already have an output plugin for this name
            fixture = self.fixtures.get(
                interfaces=[METTA_PLUGIN_INTERFACE_ROLE_OUTPUT],
                instance_id=output_key,
                exception_if_missing=False,
            )
            if fixture is not None:
                if hasattr(fixture.plugin, "set_data"):
                    fixture.plugin.set_data(output_value)
                elif hasattr(fixture.plugin, "set_text"):
                    fixture.plugin.set_text(str(output_value))

            else:
                # we only know how to create 2 kinds of outputs
                if output_type == "object":
                    fixture = self._environment.new_fixture(
                        plugin_id=METTA_PLUGIN_ID_OUTPUT_DICT,
                        instance_id=output_key,
                        priority=self._environment.plugin_priority(delta=5),
                        arguments={"data": output_value},
                        labels={
                            "parent_plugin_id": METTA_TERRAFORM_CLIENT_PLUGIN_ID,
                            "parent_instance_id": self._instance_id,
                        },
                    )
                else:
                    fixture = self._environment.new_fixture(
                        plugin_id=METTA_PLUGIN_ID_OUTPUT_TEXT,
                        instance_id=output_key,
                        priority=self._environment.plugin_priority(delta=5),
                        arguments={"text": str(output_value)},
                        labels={
                            "parent_plugin_id": METTA_TERRAFORM_CLIENT_PLUGIN_ID,
                            "parent_instance_id": self._instance_id,
                        },
                    )

                self.fixtures.add(fixture)
