import logging
import os
import importlib.util
import sys

from mirantis.testing.metta import environment_names, get_environment, discover, new_environment
from mirantis.testing.metta.plugin import Type, Factory


logger = logging.getLogger('metta.cli.base')

UCC_CLI_FIXTURE_KEY_CONFIG = 'config'

FILES = {
    'metta': 'metta.py',
    'mettac': 'mettac.py',
}


class Base:
    """ The Metta CLI program

    This CLI let's you interact with a metta environment for the purpose of
    introspection, debugging and manual interaction.

    All groups and commands come from metta CLI plugins.

    """

    def __init__(self, environment: str = ''):
        """

        Parameters:
        -----------

        environment (str) : Environment name in case you want to switch to an
            alternate environment.

        """

        # Try to make an environment using
        discover()

        try:
            if environment == '':
                environment = environment_names()[0]
        except (KeyError, IndexError) as e:
            logger.warn(
                "No environment object has been defined (making one now.) Are you in a project folder?")
            environment = 'empty'
            new_environment(environment)

        try:
            self._environment = get_environment(environment)
        except KeyError:
            raise ValueError(
                "Could not load environment '{}', not found; Existing environments: {}".format(
                    environment, environment_names()))

        # collect any comands from all discovered cli plugins
        self._collect_commands()

    def _collect_commands(self):
        """ collect commands from all cli plugins

        Create an instance of any registered cli plugin.
        From the plugin, collect the commands and add each command to this
        object directly, so that Fire can see them.

        """

        plugin_list = {}
        for plugin_id in Factory.registry[Type.CLI.value]:
            plugin_list[plugin_id] = {
                'type': Type.CLI.value,
                'plugin_id': plugin_id
            }

        for plugin in self._environment.add_fixtures_from_dict(
                plugin_list=plugin_list, type=Type.CLI).get_plugins():
            logger.info("loading cli plugin: {}".format(plugin_id))

            if hasattr(plugin, 'fire'):
                try:
                    commands = plugin.fire()
                except TypeError as e:
                    raise NotImplementedError(
                        "Plugin {} did not implement the correct fire(fixtures) interface: {}".format(
                            plugin_id, e)) from e

                if not isinstance(commands, dict):
                    raise ValueError(
                        "Plugin returned invalid commands : {}".format(commands))

                ValueError(
                    "Plugin returned invalid commands : {}".format(commands))

                for (command_name, command) in commands.items():
                    logger.debug(
                        "adding cli plugin command: {}->{}".format(plugin_id, command_name))

                    # if the command name already exists and is a dict then
                    # maybe we should merge them
                    if hasattr(self, command_name) and isinstance(
                            getattr(self, command_name), dict) and isinstance(command, dict):
                        getattr(self, command_name).update(command)
                        continue

                    setattr(self, command_name, command)
