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
from typing import List

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
        tfvars_path: str,
        binary: str = TERRAFORM_CLIENT_DEFAULT_BINARY,
    ):
        """Initialize Terraform client.

        Parameters:
        -----------
        working_dir (str) : string path to the python where the terraform root
            module/plan is, so that subprocess/tf can use that as a pwd

        state_path (str) : path to where the terraform state should be kept

        tfvars_path (str) : string path to where the vars file should be written.

        """
        self._working_dir = working_dir
        self._state_path = state_path
        self._tfvars_path = tfvars_path

        if shutil.which(binary) is None:
            raise ValueError(
                "Terraform binary not found. Terraform commands cannot be called. "
                f"Expected binary at path {binary}"
            )

        self._terraform_bin = binary

    # deep argument is an info() standard across plugins
    # pylint: disable=unused-argument
    def info(self, deep: bool = False):
        """Get info about the client plugin.

        Returns:
        --------
        Dict of keyed introspective information about the plugin.

        """
        info = {
            "working_dir": self._working_dir,
            "state_path": self._state_path,
            "tfvars_path": self._tfvars_path,
        }

        return info

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
                os.path.dirname(self._state_path), ".terraform.metta_mirantis.init.lock"
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
                        raise BlockingIOError("Timed out when waiting for init lock to go away")
            else:
                os.makedirs(os.path.dirname(os.path.abspath(lockfile)), exist_ok=True)
                with open(lockfile, "w", encoding="utf8") as lockfile_object:
                    lockfile_object.write(f"{os.getpid()} is running init")
                try:
                    self._run(["init"], with_tfvars=False, with_state=False)
                finally:
                    os.remove(lockfile)
        except subprocess.CalledProcessError as err:
            logger.error(
                "Terraform client failed to run init in %s: %s",
                self._working_dir,
                err.output,
            )
            raise Exception("Terraform client failed to run init") from err

    def plan(self):
        """Check a terraform plan."""
        try:
            self._run(["plan"], with_state=True, with_tfvars=True, return_output=False)
        except subprocess.CalledProcessError as err:
            logger.error(
                "Terraform client failed to run plan in %s: %s",
                self._working_dir,
                err.stderr,
            )
            raise RuntimeError("Terraform client failed to plan()") from err

    def apply(self, lock: bool = True):
        """Apply a terraform plan.

        Parameters:
        -----------
        lock (bool) : if False then -lock=false is passed to terraform meaning
            that the state file is ignored.

        """
        try:
            cmd: List[str] = ["apply", "-auto-approve"]
            if not lock:
                cmd.append("-lock=false")
            self._run(
                cmd,
                with_state=True,
                with_tfvars=True,
                return_output=False,
            )
        except subprocess.CalledProcessError as err:
            logger.error(
                "Terraform client failed to run apply in %s: %s",
                self._working_dir,
                err.stderr,
            )
            raise RuntimeError("Terraform client failed to run apply()") from err

    def destroy(self, lock: bool = True):
        """Remove resources that should have been created.

        Parameters:
        -----------
        lock (bool) : if False then -lock=false is passed to terraform meaning
            that the state file is ignored.

        """
        try:
            cmd: List[str] = ["destroy", "-auto-approve"]
            if not lock:
                cmd.append("-lock=false")
            self._run(
                cmd,
                with_state=True,
                with_tfvars=True,
                return_output=False,
            )
        except subprocess.CalledProcessError as err:
            logger.error(
                "Terraform client failed to run destroy() in %s: %s",
                self._working_dir,
                err.output,
            )
            raise RuntimeError("Terraform client failed to run destroy") from err

    def validate(self):
        """Validate a terraform plan."""
        try:
            self._run(
                ["validate", "-json"],
                with_state=True,
                with_tfvars=True,
                return_output=False,
            )
        except subprocess.CalledProcessError as err:
            logger.error(
                "Terraform client failed to run validate() in %s: %s",
                self._working_dir,
                err.output,
            )
            raise RuntimeError("Terraform client failed to run validate") from err

    def test(self):
        """Apply a terraform plan."""
        try:
            self._run(
                ["test"],
                with_state=True,
                with_tfvars=True,
                return_output=False,
            )
        except subprocess.CalledProcessError as err:
            logger.error(
                "Terraform client failed to run test() in %s: %s",
                self._working_dir,
                err.output,
            )
            raise RuntimeError("Terraform client failed to run test") from err

    def state(self):
        """Return the terraform state contents."""
        try:
            with open(
                os.path.join(self._working_dir, "terraform.tfstate"), encoding="utf8"
            ) as json_file:
                return json.load(json_file)
        except FileNotFoundError:
            logger.debug("Terraform client found no state file")
            return None
        except subprocess.CalledProcessError as err:
            logger.error(
                "Terraform client failed to run state() in %s: %s",
                self._working_dir,
                err.output,
            )
            raise RuntimeError("Terraform client failed to run state()") from err

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
        args: List[str] = ["output", "-json"]

        try:
            if name:
                output = self._run(args, [name], with_tfvars=False, return_output=True)
            else:
                output = self._run(args, with_tfvars=False, return_output=True)
        except subprocess.CalledProcessError as err:
            logger.error(
                "Terraform client failed to run init in %s: %s",
                self._working_dir,
                err.output,
            )
            raise RuntimeError("Terraform client failed to retrieve output") from err

        return json.loads(output)

    def _run(
        self,
        args: List[str],
        append_args: List[str] = None,
        with_state=True,
        with_tfvars=True,
        return_output=False,
    ):
        """Run terraform CLI command."""
        cmd = [self._terraform_bin]
        cmd += [f"-chdir={self._working_dir}"]
        cmd += args

        if with_tfvars and os.path.isfile(self._tfvars_path):
            cmd += [f"-var-file={self._tfvars_path}"]
        if with_state:
            cmd += [f"-state={self._state_path}"]

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
            logger.debug("running terraform command with output capture: %s", " ".join(cmd))
            res = subprocess.run(cmd, shell=False, check=True, stdout=subprocess.PIPE)
            res.check_returncode()
            return res.stdout.decode("utf-8")
