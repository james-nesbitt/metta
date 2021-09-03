"""

Metta CLI : User plugin

Examine and declare user configuration for Metta

"""
import logging
import os

import appdirs
import yaml

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta_cli.base import CliBase, cli_output

from .common_config import METTA_COMMON_APP_NAME

logger = logging.getLogger("metta.cli.user")


METTA_PLUGIN_ID_CLI_USER = "user"
""" cli plugin_id for the user plugin """


# this interface is common for all Metta plugins, but CLI plugins underuse it
# pylint: disable=too-few-public-methods
class UserCliPlugin(CliBase):
    """Metta cli command generator for commands related to the current user."""

    def fire(self):
        """Return a dict of commands."""
        return {"user": UserGroup(self._environment)}


class UserGroup:
    """Commands relating to the current user.

    These commands can be used to manage the user/system settings for defining functionality that
    should apply to all projects, at the user level.

    """

    def __init__(self, environment: Environment):
        """Add environment to command group."""
        self._environment: Environment = environment

    # deep argument is an info() standard across plugins
    # pylint: disable=unused-argument
    def info(self, deep: bool = False):
        """Output any user related information."""
        user_config = self._environment.config().load("user")
        user_config_dir = _user_path()

        info = {
            "config": user_config.get(default={}),
            "system": {
                "path": user_config_dir,
                "exists": os.path.isdir(user_config_dir),
            },
        }

        return cli_output(info)

    # pylint: disable=no-self-use
    def init(self):
        """Make a User config source that will be global for this system."""
        user_config_dir = _user_path()
        if _user_path_exists():
            raise RuntimeError(
                f"User has already been initialized on this system: {user_config_dir}"
            )

        os.mkdir(user_config_dir)

    # pylint: disable=no-self-use
    def set_id(self, uid: str):
        """Set the user id for the user on the system."""
        if not _user_path_exists():
            raise RuntimeError(
                "No user configuration has been initialized on this system.  Run `init` first"
            )

        user_config_dir = _user_path()

        config_path_user = os.path.join(user_config_dir, "user.yml")
        try:
            with open(config_path_user, "r", encoding="utf8") as user_config_file:
                user_config = yaml.load(user_config_file)
        except FileNotFoundError:
            user_config = {}

        user_config["id"] = uid

        with open(config_path_user, "w", encoding="utf8") as user_config_file:
            yaml.dump(user_config, user_config_file)


def _user_path():
    """Get path to user specific configuration."""
    # a user config path (like ~/.config/metta) may contain config
    return appdirs.user_config_dir(METTA_COMMON_APP_NAME)


def _user_path_exists():
    """Perform boolean check on whether or not the user config path exists on the system."""
    # a user config path (like ~/.config/metta) may contain config
    user_config_dir = _user_path()
    return os.path.isdir(user_config_dir)
