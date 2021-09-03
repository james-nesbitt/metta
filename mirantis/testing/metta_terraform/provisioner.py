"""

Terraform METTA provisioner plugin.

Provisioner plugin to provisioner cluster infrastructure using Terraform.

"""

import logging
import os
from typing import Any

from configerus.loaded import Loaded, LOADED_KEY_ROOT
from configerus.contrib.jsonschema.validate import (
    PLUGIN_ID_VALIDATE_JSONSCHEMA_SCHEMA_CONFIG_LABEL,
)
from configerus.validator import ValidationError

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.fixture import (
    Fixtures,
)

from .client import TerraformClientPlugin, METTA_TERRAFORM_CLIENT_PLUGIN_ID

logger = logging.getLogger("metta_terraform:provisioner")

METTA_TERRAFORM_PROVISIONER_PLUGIN_ID = "metta_terraform_provisioner"
""" Terraform provisioner plugin id """

TERRAFORM_PROVISIONER_CONFIG_LABEL = "terraform"
""" config label loading the terraform config """
TERRAFORM_PROVISIONER_CONFIG_CHART_PATH_KEY = "plan.path"
""" config key for the terraform plan path """
TERRAFORM_PROVISIONER_CONFIG_STATE_PATH_KEY = "state.path"
""" config key for the terraform state path """
TERRAFORM_PROVISIONER_CONFIG_TFVARS_KEY = "vars"
""" config key for the terraform vars Dict, which will be written to a file """
TERRAFORM_PROVISIONER_CONFIG_TFVARS_PATH_KEY = "vars_path"
""" config key for the terraform vars file path, where the plugin will write to """
TERRAFORM_PROVISIONER_DEFAULT_TFVARS_FILE = "terraform.tfvars.json"
""" Default vars file if none was specified """
TERRAFORM_PROVISIONER_DEFAULT_STATE_SUBPATH = "metta-state"
""" Default vars file if none was specified """

TERRAFORM_VALIDATE_JSONSCHEMA = {
    "type": "object",
    "properties": {
        "type": {"type": "string"},
        "plugin_id": {"type": "string"},
        "plan": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
        "state": {"type": "object", "properties": {"path": {"type": "string"}}},
        "tfvars_path": {"type": "string"},
        "tfvars": {"type": "object"},
    },
}
""" Validation jsonschema for terraform config contents """
TERRAFORM_VALIDATE_TARGET = {
    PLUGIN_ID_VALIDATE_JSONSCHEMA_SCHEMA_CONFIG_LABEL: TERRAFORM_VALIDATE_JSONSCHEMA
}
""" configerus validation target to match the above config """


# pylint: disable=too-many-instance-attributes
class TerraformProvisionerPlugin:
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
        self._environment: Environment = environment
        """ Environemnt in which this plugin exists """
        self._instance_id: str = instance_id
        """ Unique id for this plugin instance """

        self._config_label = label
        """ configerus load label that should contain all of the config """
        self._config_base = base
        """ configerus get key that should contain all tf config """

        self.fixtures: Fixtures = Fixtures()
        """Children fixtures, typically just the client plugin."""

        # Make the client fixture in the constructor.  The TF client fixture is
        # quite state safe, and should only need to be created once, unlike
        # other provisioner clients which may be vulnerable to state change.
        self.make_fixtures()

    # deep argument is an info() standard across plugins
    # pylint: disable=unused-argument
    def info(self, deep: bool = False):
        """Get info about the provisioner plugin.

        Returns:
        --------
        Dict of keyed introspective information about the plugin.

        """
        terraform_config: Loaded = self._environment.config().load(self._config_label)

        info = {
            "config": {
                "label": self._config_label,
                "base": self._config_base,
                "tfvars": terraform_config.get(
                    [self._config_base, TERRAFORM_PROVISIONER_CONFIG_TFVARS_KEY],
                    default="NONE",
                ),
                "chart_path": terraform_config.get(
                    [self._config_base, TERRAFORM_PROVISIONER_CONFIG_CHART_PATH_KEY],
                    default="MISSING",
                ),
                "state_path": terraform_config.get(
                    [self._config_base, TERRAFORM_PROVISIONER_CONFIG_STATE_PATH_KEY],
                    default="MISSING",
                ),
                "tfvars_path": terraform_config.get(
                    [self._config_base, TERRAFORM_PROVISIONER_CONFIG_TFVARS_PATH_KEY],
                    default="MISSING",
                ),
            },
            "client": {
                "instance_id": self.client_instance_id(),
            },
        }

        return info

    def prepare(self):
        """Run terraform init."""
        logger.info("Running Terraform INIT")
        self._get_client_plugin().init()

    def apply(self, lock: bool = True):
        """Create all terraform resources described in the plan."""
        logger.info("Running Terraform APPLY")
        self._get_client_plugin().apply(lock=lock)

    def destroy(self, lock: bool = True):
        """Remove all terraform resources in state."""
        logger.info("Running Terraform DESTROY")
        self._get_client_plugin().destroy(lock=lock)
        # accessing parent property for clearing out existing output fixtures
        # pylint: disable=attribute-defined-outside-init
        self.fixtures = Fixtures()

    def make_fixtures(self):
        """Make the client plugin for terraform interaction."""
        try:
            terraform_config = self._environment.config().load(
                self._config_label, force_reload=True, validator=TERRAFORM_VALIDATE_TARGET
            )
            """ get a configerus LoadedConfig for the label """
        except ValidationError as err:
            raise ValueError("Terraform config failed validation") from err

        try:
            chart_path = terraform_config.get(
                [self._config_base, TERRAFORM_PROVISIONER_CONFIG_CHART_PATH_KEY]
            )
            """ subprocess commands for terraform will be run in this path """
        except Exception as err:
            raise ValueError(
                "Plugin config did not give us a working/plan path:" f" {terraform_config.get()}"
            ) from err

        state_path = terraform_config.get(
            [self._config_base, TERRAFORM_PROVISIONER_CONFIG_STATE_PATH_KEY],
            default=os.path.join(chart_path, TERRAFORM_PROVISIONER_DEFAULT_STATE_SUBPATH),
        )
        """ terraform state path """

        tfvars = terraform_config.get(
            [self._config_base, TERRAFORM_PROVISIONER_CONFIG_TFVARS_KEY],
            default={},
        )
        """ List of vars to pass to terraform.  Will be written to a file """

        tfvars_path = terraform_config.get(
            [self._config_base, TERRAFORM_PROVISIONER_CONFIG_TFVARS_PATH_KEY],
            default=os.path.join(chart_path, TERRAFORM_PROVISIONER_DEFAULT_TFVARS_FILE),
        )
        """ vars file which will be written before running terraform """

        logger.debug("Creating Terraform client")

        fixture = self._environment.new_fixture(
            plugin_id=METTA_TERRAFORM_CLIENT_PLUGIN_ID,
            instance_id=self.client_instance_id(),
            priority=70,
            arguments={
                "chart_path": chart_path,
                "state_path": state_path,
                "tfvars": tfvars,
                "tfvars_path": tfvars_path,
            },
            labels={
                "parent_plugin_id": METTA_TERRAFORM_PROVISIONER_PLUGIN_ID,
                "parent_instance_id": self._instance_id,
            },
            replace_existing=True,
        )
        # keep this fixture attached to the workload to make it retrievable.
        self.fixtures.add(fixture, replace_existing=True)

    def client_instance_id(self) -> str:
        """Construct an instanceid for the child client plugin."""
        return f"{self._instance_id}-{METTA_TERRAFORM_CLIENT_PLUGIN_ID}"

    def _get_client_plugin(self) -> TerraformClientPlugin:
        """Retrieve the client plugin if we can."""
        return self.fixtures.get_plugin(plugin_id=METTA_TERRAFORM_CLIENT_PLUGIN_ID)
