"""

Dummy MTT provisioner plugin

"""

import logging
import json
import os
import subprocess
from typing import Dict, List

from mirantis.testing.mtt.provisioner import ProvisionerBase

logger = logging.getLogger('mirantis.testing.mtt_terraform.provisioner')

MTT_TERRAFORM_PROVISIONER_CONFIG_LABEL = 'terraform'
""" config label loading the terraform config """
MTT_TERRAFORM_PROVISIONER_CONFIG_PLAN_PATH_KEY = 'plan.path'
""" config key for the terraform plan path """
MTT_TERRAFORM_PROVISIONER_CONFIG_STATE_PATH_KEY = 'state.path'
""" config key for the terraform state path """
MTT_TERRAFORM_PROVISIONER_CONFIG_VARS_KEY = 'vars'
""" config key for the terraform vars Dict, which will be written to a file """
MTT_TERRAFORM_PROVISIONER_CONFIG_VARS_PATH_KEY = 'vars_path'
""" config key for the terraform vars file path, where the plugin will write to """
MTT_TERRAFORM_PROVISIONER_CONFIG_PATH_KEY = ''
""" config key for the terraform plan path """


MTT_TERRAFORM_PROVISIONER_DEFAULT_VARS_FILE = 'mtt_terraform.tfvars.json'
""" Default vars file if none was specified """
MTT_TERRAFORM_PROVISIONER_DEFAULT_STATE_SUBPATH = 'mtt-state'
""" Default vars file if none was specified """


class TerraformProvisionerPlugin(ProvisionerBase):
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

    def prepare(self, label:str=MTT_TERRAFORM_PROVISIONER_CONFIG_LABEL):
        """

        Interpret provided config and configure the object with all of the needed
        pieces for executing terraform commands

        """

        logger.info("Preparing Terraform setting")

        self.terraform_config = self.config.load(label)

        self.working_dir = self.terraform_config.get(MTT_TERRAFORM_PROVISIONER_CONFIG_PLAN_PATH_KEY)

        state_path = self.terraform_config.get(MTT_TERRAFORM_PROVISIONER_CONFIG_STATE_PATH_KEY, exception_if_missing=False)
        if not state_path:
            state_path = os.path.join(self.working_dir, MTT_TERRAFORM_PROVISIONER_DEFAULT_STATE_SUBPATH)

        self.vars = self.terraform_config.get(MTT_TERRAFORM_PROVISIONER_CONFIG_VARS_KEY)
        if not self.vars:
            self.vars = {}

        vars_path = self.terraform_config.get(MTT_TERRAFORM_PROVISIONER_CONFIG_VARS_PATH_KEY, exception_if_missing=False)
        if not vars_path:
            vars_path = os.path.join(self.working_dir, MTT_TERRAFORM_PROVISIONER_DEFAULT_VARS_FILE)

        logger.info("Creating Terraform client")

        self.tf = TerraformClient(working_dir=self.working_dir, state_path=state_path, vars_path=vars_path, variables=self.vars)

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

    def destroy(self):
        """ Remove all terraform resources in state """
        logger.info("Running Terraform DESTROY")
        self.tf.destroy()

    def clean(self):
        """ Remove terraform run resources from the plan """
        logger.info("Running Terraform CLEAN")
        dot_terraform = os.path.join(self.working_dir, '.terraform')
        if os.isdir(dot_terraform):
            shutil.rmtree(dot_terraform)

    """ Cluster Interaction """

    def get_output(self, name: str):
        """ retrieve an output from terraform """
        logger.debug("Retrieving terraform output '%s'", name)
        return self.tf.output(name)


class TerraformClient:
    """ Shell client for running terraform using subprocess """

    def __init__(self, working_dir: str, state_path: str, vars_path:str, variables: Dict[str, str]):
        """

        """
        self.vars = variables
        self.working_dir = working_dir
        self.state_path = state_path
        self.vars_path = vars_path

        self.terraform_bin = "terraform"
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
            lockfile = os.path.join(os.path.dirname(self.state_path), '.terraform.mtt_mirantis.init.lock')
            if os.path.exists(lockfile):
                logger.info('terraform .init lock file found.  Skipping init, but waiting for it to finish')
                time_to_wait = 120
                time_counter = 0
                while not os.path.exists(lockfile):
                    time.sleep(5)
                    time_counter += 5
                    if time_counter > time_to_wait:
                        raise BlockingIOError('Timed out when waiting for init lock to go away')
            else:
                with open(lockfile, 'w') as lockfile_object:
                    lockfile_object.write("{} is running init".format(str(os.getpid())))
                try:
                    self._run(["init"], with_vars=False, with_state=False)
                finally:
                    os.remove(lockfile)
        except subprocess.CalledProcessError as e:
            logger.error("Terraform client failed to run init in %s: %s", self.working_dir, e.output)
            raise Exception("Terraform client failed to run init") from e

    def apply(self):
        """ Apply a terraform plan """
        try:
            self._run(["apply", "-auto-approve"], with_state=True, with_vars=True, return_output=False)
        except subprocess.CalledProcessError as e:
            logger.error("Terraform client failed to run apply in %s: %s", self.working_dir, e.stderr)
            raise Exception("Terraform client failed to run apply") from e

    def destroy(self):
        """ Apply a terraform plan """
        try:
            self._run(["destroy", "-auto-approve"], with_state=True, with_vars=True, return_output=False)
        except subprocess.CalledProcessError as e:
            logger.error("Terraform client failed to run init in %s: %s", self.working_dir, e.output)
            raise Exception("Terraform client failed to run destroy") from e

    def output(self, name: str):
        """ Destroy the terraform infra """
        try:
            return self._run(['output', '-raw'], [name], with_vars=False, return_output=True)
        except subprocess.CalledProcessError as e:
            logger.error("Terraform client failed to run init in %s: %s", self.working_dir, e.output)
            raise Exception("Terraform client failed to retrieve output") from e

    def _make_vars_file(self):
        """ write the vars file """
        vars_path = self.vars_path
        os.makedirs(os.path.dirname(os.path.abspath(vars_path)), exist_ok=True)
        with open(vars_path, 'w') as var_file:
            json.dump(self.vars, var_file, sort_keys=True, indent=4)

    def _run(self, args: List[str], append_args: List[str] = [], with_state=True, with_vars=True, return_output=False):
        """ Run terraform """

        cmd = [self.terraform_bin]
        cmd += args

        if with_vars:
            self._make_vars_file()
            cmd += ["-var-file={}".format(self.vars_path)]
        if with_state:
            cmd += ["-state={}".format(self.state_path)]

        cmd += append_args

        if return_output:
            logger.debug("running terraform command with output capture: %s", " ".join(cmd))
            exec = subprocess.run(cmd, cwd=self.working_dir, shell=False, stdout=subprocess.PIPE)
            exec.check_returncode()
            return exec.stdout.decode("utf-8")
        else:
            logger.debug("running terraform command: %s", " ".join(cmd))
            exec = subprocess.run(cmd, cwd=self.working_dir, check=True, text=True)
            exec.check_returncode()
