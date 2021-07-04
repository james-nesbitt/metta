"""

Terraform METTA provisioner plugin.

Provisioner plugin to provisioner cluster infrastructure using Terraform.

"""

import logging
import os
import subprocess
import shutil
from typing import Any

from configerus.loaded import LOADED_KEY_ROOT
from configerus.contrib.jsonschema.validate import (
    PLUGIN_ID_VALIDATE_JSONSCHEMA_SCHEMA_CONFIG_LABEL,
)
from configerus.validator import ValidationError

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.fixtures import (
    Fixtures,
    METTA_FIXTURES_CONFIG_FIXTURES_LABEL,
)
from mirantis.testing.metta.provisioner import ProvisionerBase
from mirantis.testing.metta.output import METTA_PLUGIN_INTERFACE_ROLE_OUTPUT
from mirantis.testing.metta_common import (
    METTA_PLUGIN_ID_OUTPUT_DICT,
    METTA_PLUGIN_ID_OUTPUT_TEXT,
)

from .terraform import TerraformClient

logger = logging.getLogger("metta_terraform:provisioner")

METTA_TERRAFORM_PROVISIONER_PLUGIN_ID = "metta_terraform_provisioner"
""" Terraform provisioner plugin id """

TERRAFORM_PROVISIONER_CONFIG_LABEL = "terraform"
""" config label loading the terraform config """
TERRAFORM_PROVISIONER_CONFIG_ROOT_PATH_KEY = "root.path"
""" config key for a base path that should be used for any relative paths """
TERRAFORM_PROVISIONER_CONFIG_PLAN_PATH_KEY = "plan.path"
""" config key for the terraform plan path """
TERRAFORM_PROVISIONER_CONFIG_STATE_PATH_KEY = "state.path"
""" config key for the terraform state path """
TERRAFORM_PROVISIONER_CONFIG_VARS_KEY = "vars"
""" config key for the terraform vars Dict, which will be written to a file """
TERRAFORM_PROVISIONER_CONFIG_VARS_PATH_KEY = "vars_path"
""" config key for the terraform vars file path, where the plugin will write to """
TERRAFORM_PROVISIONER_DEFAULT_VARS_FILE = "metta_terraform.tfvars.json"
""" Default vars file if none was specified """
TERRAFORM_PROVISIONER_DEFAULT_STATE_SUBPATH = "metta-state"
""" Default vars file if none was specified """

TERRAFORM_VALIDATE_JSONSCHEMA = {
    "type": "object",
    "properties": {
        "type": {"type": "string"},
        "plugin_id": {"type": "string"},
        "root": {"type": "object", "properties": {"path": {"type": "string"}}},
        "plan": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
        "state": {"type": "object", "properties": {"path": {"type": "string"}}},
        "vars_path": {"type": "string"},
        "vars": {"type": "object"},
    },
}
""" Validation jsonschema for terraform config contents """
TERRAFORM_VALIDATE_TARGET = {
    PLUGIN_ID_VALIDATE_JSONSCHEMA_SCHEMA_CONFIG_LABEL: TERRAFORM_VALIDATE_JSONSCHEMA
}
""" configerus validation target to match the above config """


# pylint: disable=too-many-instance-attributes
class TerraformProvisionerPlugin(ProvisionerBase):
    """Terraform provisioner plugin.

    Provisioner plugin that allows control of and interaction with a terraform
    cluster.

    ## Requirements

    1. this plugin uses subprocess to call a terraform binary, so you have to
        install terraform in the environment

    ## Usage

    ### Plan

    The plan must exists somewhere on disk, and be accessible.

    You must specify the path and related configuration in config, which are
    read in the .prepare() execution.

    ### Vars/State

    This plugin reads TF vars from config and writes them to a vars file.  We
    could run without relying on vars file, but having a vars file allows cli
    interaction with the cluster if this plugin messes up.

    You can override where Terraform vars/state files are written to allow
    sharing of a plan across test suites.

    Parameters:
    -----------
    environment (Environment) : All metta plugins receive the environment
        object in which they were created.
    instance_id (str) : all metta plugins receive their own string identity.

    label (str) : Configerus load label for finding plugin config.
    base (str) : Configerus get base key in which the plugin should look for
        all config.

    """

    def __init__(
        self,
        environment: Environment,
        instance_id: str,
        label: str = TERRAFORM_PROVISIONER_CONFIG_LABEL,
        base: Any = LOADED_KEY_ROOT,
    ):
        """Run the super constructor but also set class properties.

        Interpret provided config and configure the object with all of the
        needed pieces for executing terraform commands

        """
        self._environment = environment
        """ Environemnt in which this plugin exists """
        self._instance_id = instance_id
        """ Unique id for this plugin instance """

        logger.info("Preparing Terraform setting")

        self.terraform_config_label = label
        """ configerus load label that should contain all of the config """
        self.terraform_config_base = base
        """ configerus get key that should contain all tf config """

        terraform_config = self._environment.config.load(self.terraform_config_label)
        """ get a configerus LoadedConfig for the terraform label """

        # Run confgerus validation on the config using our above defined
        # jsonschema
        try:
            terraform_config.get(
                self.terraform_config_base, validator=TERRAFORM_VALIDATE_TARGET
            )
        except ValidationError as err:
            raise ValueError("Terraform config failed validation") from err

        self.fixtures = self._environment.add_fixtures_from_config(
            label=self.terraform_config_label,
            base=[self.terraform_config_base, METTA_FIXTURES_CONFIG_FIXTURES_LABEL],
        )
        """ All fixtures added to this provisioner plugin. """

        self.root_path = terraform_config.get(
            [self.terraform_config_base, TERRAFORM_PROVISIONER_CONFIG_ROOT_PATH_KEY],
            default="",
        )
        """ all relative paths will have this joined as their base """

        try:
            self.working_dir = terraform_config.get(
                [self.terraform_config_base, TERRAFORM_PROVISIONER_CONFIG_PLAN_PATH_KEY]
            )
            """ subprocess commands for terraform will be run in this path """
        except Exception as err:
            raise ValueError(
                "Plugin config did not give us a working/plan path:"
                f" {terraform_config.data}"
            ) from err
        if not os.path.isabs(self.working_dir):
            if self.root_path:
                self.working_dir = os.path.join(self.root_path, self.working_dir)
            self.working_dir = os.path.abspath(self.working_dir)

        state_path = terraform_config.get(
            [self.terraform_config_base, TERRAFORM_PROVISIONER_CONFIG_STATE_PATH_KEY],
            default=os.path.join(
                self.working_dir, TERRAFORM_PROVISIONER_DEFAULT_STATE_SUBPATH
            ),
        )
        """ terraform state path """
        if not os.path.isabs(state_path):
            if self.root_path:
                state_path = os.path.join(self.root_path, state_path)
            state_path = os.path.abspath(state_path)

        self.vars = terraform_config.get(
            [self.terraform_config_base, TERRAFORM_PROVISIONER_CONFIG_VARS_KEY],
            default={},
        )
        """ List of vars to pass to terraform.  Will be written to a file """

        vars_path = terraform_config.get(
            [self.terraform_config_base, TERRAFORM_PROVISIONER_CONFIG_VARS_PATH_KEY],
            default=os.path.join(
                self.working_dir, TERRAFORM_PROVISIONER_DEFAULT_VARS_FILE
            ),
        )
        """ vars file which will be written before running terraform """
        if not os.path.isabs(vars_path):
            if self.root_path:
                vars_path = os.path.join(self.root_path, vars_path)
            vars_path = os.path.abspath(vars_path)

        logger.info("Creating Terraform client")

        self.tf_client = TerraformClient(
            working_dir=os.path.realpath(self.working_dir),
            state_path=os.path.realpath(state_path),
            vars_path=os.path.realpath(vars_path),
            variables=self.vars,
        )
        """ TerraformClient instance """

        # if the cluster is already provisioned then we can get outputs from it
        try:
            self._get_outputs_from_tf()
        except (FileNotFoundError, subprocess.CalledProcessError):
            pass

    # deep argument is an info() standard across plugins
    # pylint: disable=unused-argument
    def info(self, deep: bool = False):
        """Get info about a provisioner plugin.

        Returns:
        --------
        Dict of keyed introspective information about the plugin.

        """
        plugin = self
        client = plugin.tf_client

        info = {}
        info["plugin"] = {
            "terraform_config_label": plugin.terraform_config_label,
            "terraform_config_base": plugin.terraform_config_base,
        }
        info["client"] = {
            "vars": client.vars,
            "working_dir": client.working_dir,
            "state_path": client.state_path,
            "vars_path": client.vars_path,
            "terraform_bin": client.terraform_bin,
        }

        # build a list of helpful terraform command strings to allow users to directly run
        # terraform as we would, with the metta vars/state/working dir
        args = {
            "bin": client.terraform_bin,
            "working_dir": client.working_dir,
            "vars_path": client.vars_path,
            "state_path": client.state_path,
        }
        info["helper"] = {
            "commands": {
                "init": f"{args['bin']} -chdir={args['working_dir']} init",
                "plan": f"{args['bin']} -chdir={args['working_dir']} plan "
                f"-var-file={args['vars_path']} -state={args['state_path']}",
                "apply": f"{args['bin']} -chdir={args['working_dir']} apply "
                f"-var-file={args['vars_path']} -state={args['state_path']}",
                "destroy": f"{args['bin']} -chdir={args['working_dir']} destroy "
                f"-var-file={args['vars_path']} -state={args['state_path']}",
                "output": f"{args['bin']} -chdir={args['working_dir']} output "
                f"-state={args['state_path']}",
            }
        }

        return info

    def prepare(self):
        """Run terraform init."""
        logger.info("Running Terraform INIT : %s", self.working_dir)
        self.tf_client.init()

    def check(self):
        """Check that the terraform plan is valid."""
        logger.info("Running Terraform PLAN")
        self.tf_client.plan()

    def apply(self):
        """Create all terraform resources described in the plan."""
        logger.info("Running Terraform APPLY")
        self.tf_client.apply()
        self._get_outputs_from_tf()

    def destroy(self):
        """Remove all terraform resources in state."""
        logger.info("Running Terraform DESTROY")
        self.tf_client.destroy()
        # accessing parent property for clearing out existing output fixtures
        # pylint: disable=attribute-defined-outside-init
        self.fixtures = Fixtures()

    def clean(self):
        """Remove terraform run resources from the plan."""
        logger.info("Running Terraform CLEAN")
        dot_terraform = os.path.join(self.working_dir, ".terraform")
        if os.path.isdir(dot_terraform):
            shutil.rmtree(dot_terraform)

    # ----- Cluster Interaction -----

    def _get_outputs_from_tf(self):
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
        for output_key, output_struct in self.tf_client.output().items():

            # Here is the kind of info we can get out of terraform
            # output_sensitive = bool(output_struct['sensitive'])
            # """ Whether or not the output contains sensitive data """
            output_type = output_struct["type"][0]
            """ output primitive type (usually string|object|number) """
            # output_spec = output_struct['type'][1]
            # """ A structured spec for the type """
            output_value = output_struct["value"]
            """ output value """

            # see if we already have an output plugin for this name
            fixture = self.fixtures.get(
                interfaces=[METTA_PLUGIN_INTERFACE_ROLE_OUTPUT],
                instance_id=output_key,
                exception_if_missing=False,
            )
            if not fixture:
                # we only know how to create 2 kinds of outputs
                if output_type == "object":
                    fixture = self._environment.add_fixture(
                        plugin_id=METTA_PLUGIN_ID_OUTPUT_DICT,
                        instance_id=output_key,
                        priority=self._environment.plugin_priority(delta=5),
                        arguments={"data": output_value},
                    )
                else:
                    fixture = self._environment.add_fixture(
                        plugin_id=METTA_PLUGIN_ID_OUTPUT_TEXT,
                        instance_id=output_key,
                        priority=self._environment.plugin_priority(delta=5),
                        arguments={"text": str(output_value)},
                    )

                self.fixtures.add(fixture)
            else:
                if hasattr(fixture.plugin, "set_data"):
                    fixture.plugin.set_data(output_value)
                elif hasattr(fixture.plugin, "set_text"):
                    fixture.plugin.set_text(str(output_value))
