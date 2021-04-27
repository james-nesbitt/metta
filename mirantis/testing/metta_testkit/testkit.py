
import os
import logging
import yaml
import json
import datetime
import subprocess
import shutil
from typing import Dict, List, Any

logger = logging.getLogger('metta_testkit:testkit')

TESTKITCLIENT_CLI_CONFIG_FILE_DEFAULT = './testkit.yml'
""" Testkit config configuration file key """

TESTKITCLIENT_WORKING_DIR_DEFAULT = '.'
""" Testkit Client default working dir """
TESTKITCLIENT_BIN_PATH = '/home/james/Documents/Mirantis/tools/testkit/testkit'
""" Testkit bin exec for the subprocess """


class TestkitClient:
    """ shell client for interacting with the testkit bin """

    def __init__(self, config_file: str = TESTKITCLIENT_CLI_CONFIG_FILE_DEFAULT,
                 working_dir: str = TESTKITCLIENT_WORKING_DIR_DEFAULT,
                 debug: bool = False):
        """
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
        """ Output testkit client version """
        return self._run(['version'], return_output=True)

    def create(self, opts: Dict[str, str]):
        """ run the testkit create command """
        return self._run(['create'] + opts)

    def system_rm(self, system_name: str):
        """ remove a system from testkit """
        return self._run(['system', 'rm', system_name])

    def _run(self, args: List[str] = ['help'], return_output=False):
        """ Run a testkit command

        Parameters:

        args (List[str]) : arguments to pass to the testkit bin using
            subprocess

        """

        cmd = [self.bin, '--file={}'.format(self.config_file)]

        if self.debug:
            cmd += ['--debug']

        cmd += args

        if return_output:
            logger.debug(
                "running testkit command with output capture: %s",
                " ".join(cmd))
            exec = subprocess.run(
                cmd,
                cwd=self.working_dir,
                shell=False,
                stdout=subprocess.PIPE)
            exec.check_returncode()
            return exec.stdout.decode('utf-8')
        else:
            logger.error("running testkit command: %s", " ".join(cmd))
            exec = subprocess.run(
                cmd, cwd=self.working_dir, check=True, text=True)
            exec.check_returncode()
