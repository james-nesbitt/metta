"""

Terraform METTA provisioner plugin

"""

import logging
import json
import os
import subprocess
from typing import Dict, List, Any

from configerus.loaded import LOADED_KEY_ROOT
from configerus.contrib.jsonschema.validate import PLUGIN_ID_VALIDATE_JSONSCHEMA_SCHEMA_CONFIG_LABEL
from configerus.validator import ValidationError

from mirantis.testing.metta.plugin import METTAPlugin, Type
from mirantis.testing.metta.fixtures import Fixtures, UCCTFixturesPlugin, METTA_FIXTURES_CONFIG_FIXTURES_LABEL
from mirantis.testing.metta.provisioner import ProvisionerBase
from mirantis.testing.metta.output import OutputBase
from mirantis.testing.metta_common import METTA_PLUGIN_ID_OUTPUT_DICT, METTA_PLUGIN_ID_OUTPUT_TEXT

logger = logging.getLogger('metta.contrib.provisioner:terraform')

TERRAFORM_PROVISIONER_CONFIG_LABEL = 'terraform'
""" config label loading the terraform config """
TERRAFORM_PROVISIONER_CONFIG_ROOT_PATH_KEY = 'root.path'
""" config key for a base path that should be used for any relative paths """
TERRAFORM_PROVISIONER_CONFIG_PLAN_PATH_KEY = 'plan.path'
""" config key for the terraform plan path """
TERRAFORM_PROVISIONER_CONFIG_STATE_PATH_KEY = 'state.path'
""" config key for the terraform state path """
TERRAFORM_PROVISIONER_CONFIG_VARS_KEY = 'vars'
""" config key for the terraform vars Dict, which will be written to a file """
TERRAFORM_PROVISIONER_CONFIG_VARS_PATH_KEY = 'vars_path'
""" config key for the terraform vars file path, where the plugin will write to """
TERRAFORM_PROVISIONER_DEFAULT_VARS_FILE = 'metta_terraform.tfvars.json'
""" Default vars file if none was specified """
TERRAFORM_PROVISIONER_DEFAULT_STATE_SUBPATH = 'metta-state'
""" Default vars file if none was specified """

TERRAFORM_VALIDATE_JSONSCHEMA = {
    'type': 'object',
    'properties': {
        'type': {'type': 'string'},
        'plugin_id': {'type': 'string'},

        'root': {
            'type': 'object',
            'properties': {
                'path': {'type': 'string'}
            }
        },
        'plan': {
            'type': 'object',
            'properties': {
                'path': {'type': 'string'}
            },
            'required': ['path']
        },
        'state': {
            'type': 'object',
            'properties': {
                'path': {'type': 'string'}
            }
        },
        'vars_path': {
            'type': 'string'
        },
        'vars': {
            'type': 'object'
        }
    }
}
""" Validation jsonschema for terraform config contents """
TERRAFORM_VALIDATE_TARGET = {
    PLUGIN_ID_VALIDATE_JSONSCHEMA_SCHEMA_CONFIG_LABEL: TERRAFORM_VALIDATE_JSONSCHEMA}
""" configerus validation target to match the above config """


class TerraformProvisionerPlugin(ProvisionerBase, UCCTFixturesPlugin):
    """ Terraform provisioner plugin

    Provisioner plugin that allows control of and interaction with a terraform
    cluster.

    ## Requirements

    1. this plugin uses subprocess to call a terraform binary, so you have to install
       terraform in the environment

    ## Usage

    ### Plan

    The plan must exists somewhere on disk, and be accessible.

    You must specify the path and related configuration in config, which are read
    in the .prepare() execution.

    ### Vars/State

    This plugin reads TF vars from config and writes them to a vars file.  We
    could run without relying on vars file, but having a vars file allows cli
    interaction with the cluster if this plugin messes up.

    You can override where Terraform vars/state files are written to allow sharing
    of a plan across test suites.

    """

    def __init__(self, environment, instance_id,
                 label: str = TERRAFORM_PROVISIONER_CONFIG_LABEL, base: Any = LOADED_KEY_ROOT):
        """ Run the super constructor but also set class properties

        Interpret provided config and configure the object with all of the needed
        pieces for executing terraform commands

        """
        super(ProvisionerBase, self).__init__(environment, instance_id)

        logger.info("Preparing Terraform setting")

        self.terraform_config_label = label
        """ configerus load label that should contain all of the config """
        self.terraform_config_base = base
        """ configerus get key that should contain all tf config """

        self.terraform_config = self.environment.config.load(
            self.terraform_config_label)
        """ get a configerus LoadedConfig for the terraform label """

        # Run confgerus validation on the config using our above defined
        # jsonschema
        try:
            self.terraform_config.get(
                base, validator=TERRAFORM_VALIDATE_TARGET)
        except ValidationError as e:
            raise ValueError(
                "Terraform config failed validation: {}".format(e)) from e

        fixtures = self.environment.add_fixtures_from_config(
            label=self.terraform_config_label,
            base=[self.terraform_config_base, METTA_FIXTURES_CONFIG_FIXTURES_LABEL])
        """ All fixtures added to this provisioner plugin. """
        UCCTFixturesPlugin.__init__(self, fixtures)

        self.root_path = self.terraform_config.get([self.terraform_config_base, TERRAFORM_PROVISIONER_CONFIG_ROOT_PATH_KEY],
                                                   exception_if_missing=False)
        """ all relative paths will have this joined as their base """

        self.working_dir = self.terraform_config.get([self.terraform_config_base, TERRAFORM_PROVISIONER_CONFIG_PLAN_PATH_KEY],
                                                     exception_if_missing=False)
        """ all subprocess commands for terraform will be run in this path """
        if not self.working_dir:
            raise ValueError(
                "Plugin config did not give us a working/plan path: {}".format(self.terraform_config.data))
        if not os.path.isabs(self.working_dir):
            if self.root_path:
                self.working_dir = os.path.join(
                    self.root_path, self.working_dir)
            self.working_dir = os.path.abspath(self.working_dir)

        state_path = self.terraform_config.get([self.terraform_config_base, TERRAFORM_PROVISIONER_CONFIG_STATE_PATH_KEY],
                                               exception_if_missing=False)
        """ terraform state path """
        if not state_path:
            state_path = os.path.join(
                self.working_dir,
                TERRAFORM_PROVISIONER_DEFAULT_STATE_SUBPATH)
        if not os.path.isabs(state_path):
            if self.root_path:
                state_path = os.path.join(self.root_path, state_path)
            state_path = os.path.abspath(state_path)

        self.vars = self.terraform_config.get([self.terraform_config_base, TERRAFORM_PROVISIONER_CONFIG_VARS_KEY],
                                              exception_if_missing=False)
        """ List of vars to pass to terraform.  Will be written to a file """
        if not self.vars:
            self.vars = {}

        vars_path = self.terraform_config.get([self.terraform_config_base, TERRAFORM_PROVISIONER_CONFIG_VARS_PATH_KEY],
                                              exception_if_missing=False)
        """ vars file containing vars which will be written before running terraform """
        if not vars_path:
            vars_path = os.path.join(
                self.working_dir,
                TERRAFORM_PROVISIONER_DEFAULT_VARS_FILE)
        if not os.path.isabs(vars_path):
            if self.root_path:
                vars_path = os.path.join(self.root_path, vars_path)
            vars_path = os.path.abspath(vars_path)

        logger.info("Creating Terraform client")

        self.tf = TerraformClient(
            working_dir=os.path.realpath(self.working_dir),
            state_path=os.path.realpath(state_path),
            vars_path=os.path.realpath(vars_path),
            variables=self.vars)
        """ TerraformClient instance """

        # if the cluster is already provisioned then we can get outputs from it
        try:
            self._get_outputs_from_tf()
        except Exception:
            pass

    def info(self):
        """ get info about a provisioner plugin """
        plugin = self
        client = plugin.tf

        info = {}
        info['plugin'] = {
            'terraform_config_label': plugin.terraform_config_label,
            'terraform_config_base': plugin.terraform_config_base
        },
        info['client'] = {
            'vars': client.vars,
            'working_dir': client.working_dir,
            'state_path': client.state_path,
            'vars_path': client.vars_path,
            'terraform_bin': client.terraform_bin
        }

        fixtures = {}
        for fixture in self.get_fixtures().to_list():
            fixture_info = {
                'fixture': {
                    'type': fixture.type.value,
                    'plugin_id': fixture.plugin_id,
                    'instance_id': fixture.instance_id,
                    'priority': fixture.priority,
                }
            }
            if hasattr(fixture.plugin, 'info'):
                plugin_info = fixture.plugin.info()
                if isinstance(plugin_info, dict):
                    fixture_info.update(plugin_info)
            fixtures[fixture.instance_id] = plugin_info
        info['fixtures'] = fixtures

        info['helper'] = {
            'commands': {
                'init': "{bin} -chdir={working_dir} init".format(bin=client.terraform_bin, working_dir=client.working_dir),
                'plan': "{bin} -chdir={working_dir} plan -var-file={vars_path} -state={state_path}".format(bin=client.terraform_bin, working_dir=client.working_dir, vars_path=client.vars_path, state_path=client.state_path),
                'apply': "{bin} -chdir={working_dir} apply -var-file={vars_path} -state={state_path}".format(bin=client.terraform_bin, working_dir=client.working_dir, vars_path=client.vars_path, state_path=client.state_path),
                'destroy': "{bin} -chdir={working_dir} destroy -var-file={vars_path} -state={state_path}".format(bin=client.terraform_bin, working_dir=client.working_dir, vars_path=client.vars_path, state_path=client.state_path),
                'output': "{bin} -chdir={working_dir} output -state={state_path}".format(bin=client.terraform_bin, working_dir=client.working_dir, state_path=client.state_path)
            }
        }

        return info

    def prepare(self):
        """ run terraform init """
        logger.info("Running Terraform INIT")
        self.tf.init()

    def check(self):
        """ Check that the terraform plan is valid """
        logger.info("Running Terraform PLAN")
        self.tf.plan()

    def apply(self):
        """ Create all terraform resources described in the plan """
        logger.info("Running Terraform APPLY")
        self.tf.apply()
        self._get_outputs_from_tf()

    def destroy(self):
        """ Remove all terraform resources in state """
        logger.info("Running Terraform DESTROY")
        self.tf.destroy()
        self.fixtures = Fixtures()

    def clean(self):
        """ Remove terraform run resources from the plan """
        logger.info("Running Terraform CLEAN")
        dot_terraform = os.path.join(self.working_dir, '.terraform')
        if os.isdir(dot_terraform):
            shutil.rmtree(dot_terraform)

    """ Cluster Interaction """

    def _get_outputs_from_tf(self) -> Fixtures:
        """ retrieve an output from terraform

        For other METTA plugins we can just load configuration, and creating
        output plugin instances from various value in config.

        We do that here, but  we also want to check of any outputs exported by
        the terraform root module, which we get using the tf client.

        If we find a root module output without a matching config output
        defintition then we make some assumptions about plugin type and add it
        to the list. We make some simple investigation into output plugin types
        and pick either the contrib.common.dict or contrib.common.text plugins.

        If we find a root module output that matches an output that was declared
        in config then we use that.  This allows config to define a plugin_id
        which will then be populated automatically.  If you know what type of
        data you are expecting from a particular tf output then you can prepare
        and config for it to do things like setting default values.

        Priorities can be used in the config.

        Returns:
        --------

        A Fixtures set of plugins.

        """

        # now we ask TF what output it nows about and merge together those as
        # new output plugins.
        # tf.outputs() produces a list of (sensitive:bool, type: [str,  object,
        # value:Any])
        for output_key, output_struct in self.tf.output().items():
            # we only know how to create 2 kinds of outputs
            output_sensitive = bool(output_struct['sensitive'])
            """ Whether or not the output contains sensitive data """
            output_type = output_struct['type'][0]
            """ String output primitive type (usually string|object|number) """
            output_spec = output_struct['type'][1]
            """ A structured spec for the type """
            output_value = output_struct['value']
            """ output value """

            # see if we already have an output plugin for this name
            fixture = self.fixtures.get_fixture(
                type=Type.OUTPUT,
                instance_id=output_key,
                exception_if_missing=False)
            if not fixture:
                if output_type == 'object':
                    fixture = self.environment.add_fixture(
                        type=Type.OUTPUT,
                        plugin_id=METTA_PLUGIN_ID_OUTPUT_DICT,
                        instance_id=output_key,
                        priority=self.environment.plugin_priority(delta=5),
                        arguments={'data': output_value})
                else:
                    fixture = self.environment.add_fixture(
                        type=Type.OUTPUT,
                        plugin_id=METTA_PLUGIN_ID_OUTPUT_TEXT,
                        instance_id=output_key,
                        priority=self.environment.plugin_priority(delta=5),
                        arguments={'text': str(output_value)})

                self.fixtures.add_fixture(fixture)
            else:
                if hasattr(fixture.plugin, 'set_data'):
                    fixture.plugin.set_data(output_value)
                elif hasattr(fixture.plugin, 'set_text'):
                    fixture.plugin.set_text(str(output_value))


class TerraformClient:
    """ Shell client for running terraform using subprocess """

    def __init__(self, working_dir: str, state_path: str,
                 vars_path: str, variables: Dict[str, str]):
        """

        Parameters:
        -----------

        working_dir (str) : string path to the python where the terraform root
            module/plan is, so that subprocess/tf can use that as a pwd

        state_path (str) : path to where the terraform state should be kept

        vars_path (str) : string path to where the vars file should be written.

        variables (Dict[str,str]) : terraform variables dict which will be
            written to a vars file.

        """
        self.vars = variables
        self.working_dir = working_dir
        self.state_path = state_path
        self.vars_path = vars_path

        self.terraform_bin = 'terraform'
        pass

    def state(self):
        """ return the terraform state contents """
        try:
            with open(os.path.join(self.working_dir, 'terraform.tfstate')) as json_file:
                return json.load(json_file)
        except FileNotFoundError:
            logger.debug("Terraform client found no state file")
            return None

    def init(self):
        """ run terraform init

        init is something that can be run once for a number of jobs in parallel
        we lock the process. If a lock is in place, then we just wait for an
        unlock and return.
        Other terraform actions lock themselves, and we want to fail if the
        operation is locked, but here we just want to skip it.

        """
        try:
            lockfile = os.path.join(
                os.path.dirname(
                    self.state_path),
                '.terraform.metta_mirantis.init.lock')
            if os.path.exists(lockfile):
                logger.info(
                    "terraform .init lock file found.  Skipping init, but waiting for it to finish")
                time_to_wait = 120
                time_counter = 0
                while not os.path.exists(lockfile):
                    time.sleep(5)
                    time_counter += 5
                    if time_counter > time_to_wait:
                        raise BlockingIOError(
                            "Timed out when waiting for init lock to go away")
            else:
                os.makedirs(
                    os.path.dirname(
                        os.path.abspath(lockfile)),
                    exist_ok=True)
                with open(lockfile, 'w') as lockfile_object:
                    lockfile_object.write(
                        "{} is running init".format(str(os.getpid())))
                try:
                    self._run(['init'], with_vars=False, with_state=False)
                finally:
                    os.remove(lockfile)
        except subprocess.CalledProcessError as e:
            logger.error(
                "Terraform client failed to run init in %s: %s",
                self.working_dir,
                e.output)
            raise Exception("Terraform client failed to run init") from e

    def apply(self):
        """ Apply a terraform plan """
        try:
            self._run(['apply', '-auto-approve'], with_state=True,
                      with_vars=True, return_output=False)
        except subprocess.CalledProcessError as e:
            logger.error(
                "Terraform client failed to run apply in %s: %s",
                self.working_dir,
                e.stderr)
            raise Exception(
                "Terraform client failed to run : {}".format(e)) from e

    def destroy(self):
        """ Apply a terraform plan """
        try:
            self._run(['destroy', '-auto-approve'], with_state=True,
                      with_vars=True, return_output=False)
        except subprocess.CalledProcessError as e:
            logger.error(
                "Terraform client failed to run init in %s: %s",
                self.working_dir,
                e.output)
            raise Exception("Terraform client failed to run destroy") from e

    def output(self, name: str = ''):
        """ Retrieve terraform outputs

        Run the terraform output command, to retrieve all or one of the outputs.
        Outputs are returned always as json as it is the only way to machine
        parse outputs properly.

        Returns:
        --------

        If you provided a name, then a single output is returned, otherwise a
        dict of outputs is returned.


        """
        args = ['output', '-json']
        """ collect subprocess args to pass """

        try:
            if name:
                output = self._run(
                    args, [name], with_vars=False, return_output=True)
            else:
                output = self._run(args, with_vars=False, return_output=True)
        except subprocess.CalledProcessError as e:
            logger.error(
                "Terraform client failed to run init in %s: %s",
                self.working_dir,
                e.output)
            raise Exception(
                "Terraform client failed to retrieve output") from e

        return json.loads(output)

    def _make_vars_file(self):
        """ write the vars file """
        vars_path = self.vars_path

        try:
            os.makedirs(
                os.path.dirname(
                    os.path.abspath(vars_path)),
                exist_ok=True)
            with open(vars_path, 'w') as var_file:
                json.dump(self.vars, var_file, sort_keys=True, indent=4)
        except Exception as e:
            raise Exception(
                "Could not create terraform vars file: {} : {}".format(
                    vars_path, e)) from e

    def _run(self, args: List[str], append_args: List[str] = [
    ], with_state=True, with_vars=True, return_output=False):
        """ Run terraform """

        cmd = [self.terraform_bin]
        cmd += args

        if with_vars:
            self._make_vars_file()
            cmd += ['-var-file={}'.format(self.vars_path)]
        if with_state:
            cmd += ['-state={}'.format(self.state_path)]

        cmd += append_args

        if return_output:
            logger.debug(
                "running terraform command with output capture: %s",
                " ".join(cmd))
            exec = subprocess.run(
                cmd,
                cwd=self.working_dir,
                shell=False,
                stdout=subprocess.PIPE)
            exec.check_returncode()
            return exec.stdout.decode('utf-8')
        else:
            logger.debug("running terraform command: %s", " ".join(cmd))
            exec = subprocess.run(
                cmd, cwd=self.working_dir, check=True, text=True)
            exec.check_returncode()
