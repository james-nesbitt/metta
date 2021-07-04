"""

Metta CLI : Environment commands.

Various commands that allow introspection of the available environments.

"""
import logging

from mirantis.testing.metta import environment_names, get_environment
from mirantis.testing.metta.environment import Environment

from .base import CliBase, cli_output

logger = logging.getLogger("metta.cli.environment")


# this interface is common for all Metta plugins, but CLI plugins underuse it
# pylint: disable=too-few-public-methods
class EnvironmentCliPlugin(CliBase):
    """Fire command/group generator for environment commands."""

    def fire(self):
        """Return a dict of commands."""
        return {"environment": EnvironmentGroup(self._environment)}


class EnvironmentGroup:
    """Base Fire command group for environment commands."""

    def __init__(self, environment: Environment):
        """Create CLI command group."""
        self._environment = environment

    # needs to be a method for registration in fire
    # pylint: disable=no-self-use
    def list(self, raw: bool = False):
        """List all of the environment names."""
        names = environment_names()
        if raw:
            return names
        return cli_output(names)

    def _get_environment(self, environment: str = ""):
        """Select an environment."""
        if not environment:
            return self._environment
        return get_environment(environment)

    def name(self, environment: str = ""):
        """Return env name."""
        environment_object = self._get_environment(environment)
        return environment_object.name

    def info(self, environment: str = ""):
        """Return info about an environment."""
        environment_object = self._get_environment(environment)

        info = {"name": environment_object.name}

        if len(environment_object.states) > 0:
            info["states"] = {
                "available": environment_object.states,
                "active": environment_object.state,
            }

        return cli_output(info)

    def bootstraps(self, environment: str = ""):
        """List bootstraps that have been applied to the environment."""
        environment_object = self._get_environment(environment)
        bootstrap_list = list(
            bootstrap for bootstrap in environment_object.bootstrapped
        )

        return cli_output(bootstrap_list)
