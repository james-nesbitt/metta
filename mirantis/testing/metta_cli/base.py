import logging
import os
import importlib.util
import sys

from mirantis.testing.metta import environment_names, get_environment, new_environment
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

        self._paths = {}
        """ key value pair of paths to module namespaces where we can look for injection """

        # Look for any paths that we can use to source init code
        self._add_project_root_path()
        # run any init code found in _paths to get ourselves in a state that
        # matches a project
        self._project_init()

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

    def _project_init(self):
        """ initialize the project by looking for path base injections

        Look for any of our cli module files, and if found import/exec them
        using core Python module management.

        The modules are expected to interact directly METTA environments, which
        the CLI will then discover.

        """
        if len(self._paths):
            for (path_module_name, path) in self._paths.items():
                for (file_module_name, file) in FILES.items():
                    module_name = '{}.{}'.format(
                        path_module_name, path_module_name)
                    module_path = os.path.join(path, file)

                    logger.debug(
                        "Checking for fixtures in: {}".format(module_path))

                    if os.path.isfile(module_path):

                        if path not in sys.path:
                            sys.path.append(path)

                        spec = importlib.util.spec_from_file_location(
                            module_name, module_path)
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)

                        # Note that the module is responsible for interacting
                        # directly with METTA and creating environments that
                        # The CLI will interact with

    def _add_project_root_path(self):
        """ Find a string path to the project root

        Start at the cwd() and search upwards until we find a path that contains
        one of the Marker files in FILES

        """

        check_path = os.path.abspath(os.getcwd())
        while check_path:
            if check_path == '/':
                break

            for marker_file in FILES.values():
                marker_path = os.path.join(check_path, marker_file)
                if os.path.isfile(marker_path):
                    self._paths['pwd'] = check_path
                    return
            check_path = os.path.dirname(check_path)
