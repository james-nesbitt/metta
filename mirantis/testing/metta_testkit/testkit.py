"""

Testkit command line tool caller.

"""
import logging
import subprocess
import json
from typing import List


logger = logging.getLogger('metta_testkit:testkit')

TESTKITCLIENT_CLI_CONFIG_FILE_DEFAULT = './testkit.yml'
""" Testkit config configuration file key """

TESTKITCLIENT_WORKING_DIR_DEFAULT = '.'
""" Testkit Client default working dir """
TESTKITCLIENT_BIN_PATH = '/home/james/Documents/Mirantis/tools/testkit/testkit'
""" Testkit bin exec for the subprocess """


class TestkitClient:
    """Shell client for interacting with the testkit bin."""

    def __init__(self, config_file: str = TESTKITCLIENT_CLI_CONFIG_FILE_DEFAULT,
                 working_dir: str = TESTKITCLIENT_WORKING_DIR_DEFAULT,
                 debug: bool = False):
        """Initialize Testkit command executer.

        Parameters:
        -----------
        config_file (str) : path to testkit config file, typically
            testkit.yml

        debug (bool) : passed to the testkit client to tell it to enable
            verbose debugging output.

        """
        self.config_file = config_file
        """ Path to config file """
        self.working_dir = working_dir
        """ Python subprocess working dir to execute testkit in.
            This may be relevant in cases where ssh keys have a relative path """

        self.debug = debug
        """ should testkit be run with verbose output enabled ? """

        self.bin = TESTKITCLIENT_BIN_PATH
        """ path to testkit executable """

    def version(self):
        """Return testkit client version."""
        return self._run(['version'], return_output=True, use_config_file=False)

    def create(self, opts: List[str]):
        """Run the testkit create command."""
        return self._run(['create'] + opts)

    def system_ls(self):
        """List all of the systems testkit can see using our config."""
        return json.loads(self._run(['system', 'ls', '--json'], return_output=True))

    def system_rm(self, system_name: str):
        """Remove a system from testkit."""
        return self._run(['system', 'rm', system_name])

    def machine_ls(self, system_name: str):
        """Remove a system from testkit."""
        return json.loads(self._run(['machine', 'ls', '--filter', f'name={system_name}', '--json'],
                          return_output=True))

    # this syntax makes it easier to read
    # pylint: disable=inconsistent-return-statements
    def _run(self, args: List[str], return_output=False, use_config_file: bool = True):
        """Run a testkit command.

        Parameters:
        -----------
        args (List[str]) : arguments to pass to the testkit bin using
            subprocess

        """
        cmd = [self.bin]

        if use_config_file:
            cmd += [f'--file={self.config_file}']

        if self.debug:
            cmd += ['--debug']

        cmd += args

        if not return_output:
            logger.debug("running testkit command: %s", " ".join(cmd))
            res = subprocess.run(cmd, cwd=self.working_dir, text=True, check=True)
            res.check_returncode()
        else:
            logger.debug("running testkit command with output capture: %s", " ".join(cmd))
            res = subprocess.run(cmd, cwd=self.working_dir, shell=False, stdout=subprocess.PIPE,
                                 check=True)
            res.check_returncode()
            return res.stdout.decode('utf-8')
