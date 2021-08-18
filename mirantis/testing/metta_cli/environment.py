"""

Metta CLI : Environment commands.

Various commands that allow introspection of the available environments.

"""
import logging

from mirantis.testing.metta.globals import global_fixtures
from mirantis.testing.metta.environment import Environment, METTA_PLUGIN_INTERFACE_ROLE_ENVIRONMENT

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
        self._environment: Environment = environment

    # needs to be a method for registration in fire
    # pylint: disable=no-self-use
    def list(self, raw: bool = False):
        """List all of the environment names."""
        names = [
            fixture.instance_id
            for fixture in global_fixtures.filter(
                interfaces=[METTA_PLUGIN_INTERFACE_ROLE_ENVIRONMENT]
            )
        ]
        if raw:
            return names
        return cli_output(names)

    def _get_environment(self, environment: str = ""):
        """Select an environment."""
        if not environment:
            environment = self._environment.instance_id()
        return global_fixtures.get(
            instance_id=environment, interfaces=[METTA_PLUGIN_INTERFACE_ROLE_ENVIRONMENT]
        )

    def name(self, environment: str = ""):
        """Return env name."""
        environment_plugin = self._get_environment(environment).plugin
        return environment_plugin.instance_id()

    def info(self, environment: str = "", deep: bool = False):
        """Return info about an environment."""
        environment_fixture = self._get_environment(environment)

        return cli_output(environment_fixture.info(deep=deep))

    def bootstraps(self, environment: str = ""):
        """List bootstraps that have been applied to the environment."""
        environment_plugin = self._get_environment(environment).plugin
        # pylint: disable=protected-access
        bootstrap_list = list(bootstrap for bootstrap in environment_plugin._environment_boostraps)

        return cli_output(bootstrap_list)
