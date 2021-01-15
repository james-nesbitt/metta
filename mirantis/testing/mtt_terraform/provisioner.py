"""

Terraform MTT provisioner pluging

@TODO

1. faster init by avoiding running tf.init() ?

"""

import logging
import json
import os.path
import subprocess
from typing import Dict, List

logger = logging.getLogger("mirantis.testing.mtt_terraform.provisioner")

class TerraformProvisioner:
    """ Dummy provisioner class """

    def __init__(self, conf):
        """

        Parameters:

        conf (mirantis.testing.toolbox.config.Config):
            A config object which can be used to load all terraform related
            config.
        """
        self.conf = conf
        self.terraform_config = conf.load("terraform")

        self.working_dir = self.terraform_config.get("plan.path")
        # assert self.working_dir, "No terraform plan path was provided in the terraform configuration"

        state_path = self.terraform_config.get("state.path", exception_if_missing=False)
        if not state_path:
            state_path = os.path.join(self.working_dir, "mtt-state")

        self.vars = self.terraform_config.get("vars")
        if not self.vars:
            self.vars = {}

        vars_path = self.terraform_config.get("vars_path", exception_if_missing=False)
        if not vars_path:
            vars_path = os.path.join(self.working_dir, "mtt_terraform.tfvars.json")

        self.tf = TerraformClient(working_dir=self.working_dir, state_path=state_path, vars_path=vars_path, variables=self.vars)


    def prepare(self):
        """ preapre cluster for up """
        logger.info("Running Terraform INIT")
        self.tf.init()

    def check(self):
        """ pretend to bring a cluster up """
        logger.info("Running Terraform PLAN")
        self.tf.plan()

    def up(self):
        """ pretend to bring a cluster up """
        logger.info("Running Terraform APPLY")
        self.tf.apply()

    def down(self):
        """ pretend to brind a cluster down """
        logger.info("Running Terraform DESTROY")
        self.tf.destroy()

    def output(self, name: str):
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
        """ run terraform init """
        try:
            self._run(["init"], with_vars=False, with_state=False)
        except subprocess.CalledProcessError as e:
            logger.error("Terraform client failed to run init in %s: %s", self.working_dir, e.stdout)
            raise e

    def apply(self):
        """ Apply a terraform plan """
        try:
            self._run(["apply", "-auto-approve"], with_state=True, with_vars=True, return_output=False)
        except subprocess.CalledProcessError as e:
            logger.error("Terraform client failed to run init in %s: %s", self.working_dir, e.stdout)
            raise e


    def destroy(self):
        """ Apply a terraform plan """
        try:
            self._run(["destroy", "-auto-approve"], with_state=True, with_vars=True, return_output=False)
        except subprocess.CalledProcessError as e:
            logger.error("Terraform client failed to run init in %s: %s", self.working_dir, e.stdout)
            raise e

    def output(self, name: str):
        """ Destroy the terraform infra """
        try:
            return self._run(["output", "-raw"], [name], with_vars=False, return_output=True)
        except subprocess.CalledProcessError as e:
            logger.error("Terraform client failed to run init in %s: %s", self.working_dir, e.stdout)
            raise e

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
            exec = subprocess.run(cmd, cwd=self.working_dir)
            exec.check_returncode()
