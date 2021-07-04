"""

Terraform clie handler.

Here are is all of the functionality which actually runs terraform commands
on the command line using subprocess.

"""

import logging
import json
import os
import time
import subprocess
import shutil
from typing import Dict, List

logger = logging.getLogger("metta_terraform:client")

TERRAFORM_CLIENT_DEFAULT_BINARY = "terraform"
""" default terraform executable for subprocess """


class TerraformClient:
    """Shell client for running terraform using subprocess."""

    # this is what it takes to configure the terraform client
    # pylint: disable=too-many-arguments
    def __init__(
        self,
        working_dir: str,
        state_path: str,
        vars_path: str,
        variables: Dict[str, str],
        binary: str = TERRAFORM_CLIENT_DEFAULT_BINARY,
    ):
        """Initialize Terraform client.

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

        if shutil.which(binary) is None:
            raise ValueError(
                f"Terraform binary not found. Terraform commands cannot be called.  Expected binary at path {binary}"
            )

        self.terraform_bin = binary

    def state(self):
        """Return the terraform state contents."""
        try:
            with open(os.path.join(self.working_dir, "terraform.tfstate")) as json_file:
                return json.load(json_file)
        except FileNotFoundError:
            logger.debug("Terraform client found no state file")
            return None

    def init(self):
        """Run terraform init.

        init is something that can be run once for a number of jobs in parallel
        we lock the process. If a lock is in place, then we just wait for an
        unlock and return.
        Other terraform actions lock themselves, and we want to fail if the
        operation is locked, but here we just want to skip it.

        """
        try:
            lockfile = os.path.join(
                os.path.dirname(self.state_path), ".terraform.metta_mirantis.init.lock"
            )
            if os.path.exists(lockfile):
                logger.info(
                    "terraform .init lock file found.  Skipping init, but waiting for it to finish"
                )
                time_to_wait = 120
                time_counter = 0
                while not os.path.exists(lockfile):
                    time.sleep(5)
                    time_counter += 5
                    if time_counter > time_to_wait:
                        raise BlockingIOError(
                            "Timed out when waiting for init lock to go away"
                        )
            else:
                os.makedirs(os.path.dirname(os.path.abspath(lockfile)), exist_ok=True)
                with open(lockfile, "w") as lockfile_object:
                    lockfile_object.write(f"{os.getpid()} is running init")
                try:
                    self._run(["init"], with_vars=False, with_state=False)
                finally:
                    os.remove(lockfile)
        except subprocess.CalledProcessError as err:
            logger.error(
                "Terraform client failed to run init in %s: %s",
                self.working_dir,
                err.output,
            )
            raise Exception("Terraform client failed to run init") from err

    def apply(self):
        """Apply a terraform plan."""
        try:
            self._run(
                ["apply", "-auto-approve"],
                with_state=True,
                with_vars=True,
                return_output=False,
            )
        except subprocess.CalledProcessError as err:
            logger.error(
                "Terraform client failed to run apply in %s: %s",
                self.working_dir,
                err.stderr,
            )
            raise RuntimeError("Terraform client failed to run") from err

    def plan(self):
        """Check a terraform plan."""
        try:
            self._run(["plan"], with_state=True, with_vars=True, return_output=False)
        except subprocess.CalledProcessError as err:
            logger.error(
                "Terraform client failed to run plan in %s: %s",
                self.working_dir,
                err.stderr,
            )
            raise RuntimeError("Terraform client failed to plan") from err

    def destroy(self):
        """Apply a terraform plan."""
        try:
            self._run(
                ["destroy", "-auto-approve", "-lock=false"],
                with_state=True,
                with_vars=True,
                return_output=False,
            )
            self._rm_vars_file()
        except subprocess.CalledProcessError as err:
            logger.error(
                "Terraform client failed to run init in %s: %s",
                self.working_dir,
                err.output,
            )
            raise RuntimeError("Terraform client failed to run destroy") from err

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
        args = ["output", "-json"]
        """ collect subprocess args to pass """

        try:
            if name:
                output = self._run(args, [name], with_vars=False, return_output=True)
            else:
                output = self._run(args, with_vars=False, return_output=True)
        except subprocess.CalledProcessError as err:
            logger.error(
                "Terraform client failed to run init in %s: %s",
                self.working_dir,
                err.output,
            )
            raise RuntimeError("Terraform client failed to retrieve output") from err

        return json.loads(output)

    def _make_vars_file(self):
        """Write the vars file."""
        vars_path = self.vars_path

        try:
            os.makedirs(os.path.dirname(os.path.abspath(vars_path)), exist_ok=True)
            with open(vars_path, "w") as var_file:
                json.dump(self.vars, var_file, sort_keys=True, indent=4)
        except Exception as err:
            raise RuntimeError(
                f"Could not create terraform vars file: {vars_path}"
            ) from err

    def _rm_vars_file(self):
        """Remove any created vars file."""
        vars_path = self.vars_path
        if os.path.isfile(vars_path):
            os.remove(vars_path)

    def _run(
        self,
        args: List[str],
        append_args: List[str] = None,
        with_state=True,
        with_vars=True,
        return_output=False,
    ):
        """Run terraform CLI command."""
        cmd = [self.terraform_bin]
        cmd += [f"-chdir={self.working_dir}"]
        cmd += args

        if with_vars:
            self._make_vars_file()
            cmd += [f"-var-file={self.vars_path}"]
        if with_state:
            cmd += [f"-state={self.state_path}"]

        if append_args is not None:
            cmd += append_args

        # improve readability
        # pylint: disable=no-else-return
        if not return_output:
            logger.debug("running terraform command: %s", " ".join(cmd))
            res = subprocess.run(cmd, check=True, text=True)
            res.check_returncode()
            return res
        else:
            logger.debug(
                "running terraform command with output capture: %s", " ".join(cmd)
            )
            res = subprocess.run(cmd, shell=False, check=True, stdout=subprocess.PIPE)
            res.check_returncode()
            return res.stdout.decode("utf-8")
