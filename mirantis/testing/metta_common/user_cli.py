"""

Metta CLI : User plugin

Examine and declare user configuration for Metta

"""
import logging
import appdirs
import os
from typing import Dict, Any, List

import json
import yaml

from mirantis.testing.metta.plugin import Type
from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.cli import CliBase

from .common_config import METTA_COMMON_APP_NAME

logger = logging.getLogger('metta.cli.user')


class UserCliPlugin(CliBase):

    def fire(self):
        """ return a dict of commands """
        return {
            'user': UserGroup(self.environment)
        }


class UserGroup():

    def __init__(self, environment: Environment):
        self._environment = environment

    def info(self):
        """ Output any user related information """
        user_config = self._environment.config.load('user')
        user_config_dir = self._user_path()

        info = {
            'config': user_config.get(default={}),
            'system': {
                'path': user_config_dir,
                'exists': os.path.isdir(user_config_dir)
            }
        }

        return json.dumps(info, indent=2)

    def init(self):
        """ Make a User config source that will be global for this system """
        user_config_dir = self._user_path()
        if self._user_path_exists():
            raise RuntimeError(
                "User has already been initialized on this system: {}".format(user_config_dir))

        os.mkdir(user_config_dir)

    # @TODO generate a more abstract method for setting values
    def set_id(self, id: str):
        """ set the user id for the user on the system """
        if not self._user_path_exists():
            raise RuntimeError(
                "No user configuration has been initialized on this system.  Run `init` first")

        user_config_dir = self._user_path()

        config_path_user = os.path.join(user_config_dir, 'user.yml')
        try:
            with open(config_path_user, 'r') as user_config_file:
                user_config = yaml.load(user_config_file)
        except FileNotFoundError:
            user_config = {}

        user_config['id'] = id

        with open(config_path_user, 'w') as user_config_file:
            yaml.dump(user_config, user_config_file)

    def _user_path(self):
        """ path to user specific configuration """
        # a user config path (like ~/.config/metta) may contain config
        return appdirs.user_config_dir(METTA_COMMON_APP_NAME)

    def _user_path_exists(self):
        """ boolean check on whether or not the user config path exists on the system """
        # a user config path (like ~/.config/metta) may contain config
        user_config_dir = self._user_path()
        return os.path.isdir(user_config_dir)
