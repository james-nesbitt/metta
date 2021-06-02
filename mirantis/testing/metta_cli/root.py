"""

CLI Plugins base.

@TODO move to the metta_cli package

Define a base class and some constants for the CLI plugins.  The CLI plugins provide functionality
for the metta cli tool, which is provided by the metta_cli package.  This is here because the plugin
types are defined as an enum in this package, and so the base class is here too.

"""
import logging

from mirantis.testing.metta import environment_names, get_environment, discover, new_environment
from mirantis.testing.metta.plugin import Factory

from .base import METTA_PLUGIN_TYPE_CLI


logger = logging.getLogger('metta.cli.root')


# This gets used to collect public properties dynamically.
# pylint: disable=too-few-public-methods
class Root:
    """The Metta CLI program.

    This CLI let's you interact with a metta environment for the purpose of
    introspection, debugging and manual interaction.

    All groups and commands come from metta CLI plugins.

    """

    def __init__(self, environment: str = '', state: str = ''):
        """Configure initial root object.

        Parameters:
        -----------
        environment (str) : Environment name in case you want to switch to an
            alternate environment.

        state (str) : Environment state to consider active.  Will throw an error
            if the state doesn't exist for the selected environment.

        """
        # Try to make an environment using the core discover approach.  This looks for a metta.yml
        # file and uses it as a config source, to load all other configuration.
        discover()

        try:
            if environment == '':
                environment = environment_names()[0]
        except (KeyError, IndexError):
            logger.warning("No environment object has been defined (making one now.) "
                           "Are you in a project folder?")
            environment = 'empty'
            new_environment(environment)

        try:
            self._environment = get_environment(environment)

            if state:
                self._environment.set_state(state)
        except KeyError as err:
            raise ValueError(f"Could not load environment '{environment}', not found") from err

        # collect any comands from all discovered cli plugins
        self._collect_commands()

    def _collect_commands(self):
        """Collect commands from all cli plugins.

        Create an instance of any registered cli plugin.
        From the plugin, collect the commands and add each command to this
        object directly, so that Fire can see them.

        """
        for plugin_id in Factory.registry[METTA_PLUGIN_TYPE_CLI]:
            plugin_dict = {
                'plugin_type': METTA_PLUGIN_TYPE_CLI,
                'plugin_id': plugin_id
            }

            fixture = self._environment.add_fixture_from_dict(plugin_dict=plugin_dict)

            logger.info("loading cli plugin: %s", fixture.plugin_id)
            plugin = fixture.plugin

            if not hasattr(plugin, 'fire'):
                continue

            try:
                commands = plugin.fire()
            except TypeError as err:
                raise NotImplementedError(f"Plugin {plugin.plugin_id} did not properly implement "
                                          f"the fire(fixtures) method") from err

            if not isinstance(commands, dict):
                raise ValueError(f"Plugin returned invalid commands : {commands}")

            # Attach any found commands/groups to this object
            for (command_name, command) in commands.items():
                logger.debug("adding cli plugin command/group: %s->%s",
                             fixture.plugin_id,
                             command_name)

                # if the command name already exists and is a dict then
                # maybe we should merge them
                if hasattr(self, command_name) and isinstance(
                        getattr(self, command_name), dict) and isinstance(command, dict):
                    getattr(self, command_name).update(command)
                    continue

                setattr(self, command_name, command)
