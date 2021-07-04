"""

An environment is meant to represent a testable cluster as a testing harness.

In METTA an environment is a single configerus Config object and a set of
METTA plugins in a manageable set.

METTA uses the Fixtures object to manage a set of plugins, which allows us to
mix a bunch of plugin objects together and manage them.

@NOTE states were just recently added and are currently inelegant and
    inefficient but should get a refactor soon.

"""
import logging
import random
import string
from typing import List, Dict, Any, Union
from importlib import metadata

from configerus.config import Config
from configerus.loaded import Loaded, LOADED_KEY_ROOT
from configerus.validator import ValidationError
from configerus.contrib.jsonschema import PLUGIN_ID_VALIDATE_JSONSCHEMA
from configerus.contrib.files import PLUGIN_ID_SOURCE_PATH, CONFIGERUS_PATH_KEY
from configerus.contrib.dict import PLUGIN_ID_SOURCE_DICT, CONFIGERUS_DICT_DATA_KEY
from configerus.contrib.env import (
    PLUGIN_ID_SOURCE_ENV_SPECIFIC,
    CONFIGERUS_ENV_SPECIFIC_BASE_KEY,
    PLUGIN_ID_SOURCE_ENV_JSON,
    CONFIGERUS_ENV_JSON_ENV_KEY,
)

from .plugin import (
    Factory,
    METTA_PLUGIN_CONFIG_KEY_PLUGINID,
    METTA_PLUGIN_CONFIG_KEY_INSTANCEID,
    METTA_PLUGIN_CONFIG_KEY_ARGUMENTS,
)
from .fixtures import (
    Fixture,
    Fixtures,
    METTA_FIXTURE_CONFIG_KEY_PRIORITY,
    METTA_FIXTURES_CONFIG_FIXTURES_LABEL,
    METTA_FIXTURE_VALIDATION_JSONSCHEMA,
)

logger = logging.getLogger("metta.environment")

DEFAULT_PLUGIN_PRIORITY = 70
""" Default plugin priority when turned into a fixture """

FIXTURE_VALIDATION_TARGET_FORMAT_STRING = "jsonschema:{key}"
""" python string .format template for string jsonchema configerus formatter definition """

METTA_BOOTSTRAP_ENTRYPOINT = "metta.bootstrap"
""" SetupTools entry_point used for METTA bootstrap """

METTA_PLUGIN_CONFIG_LABEL_ENVIRONMENTS = "environments"
""" config label discover a list of environments in a loaded config """
METTA_PLUGIN_CONFIG_KEY_ENVIRONMENTS = "environments"
""" this key could be used to discover a list of environments in a loaded config """
METTA_PLUGIN_CONFIG_KEY_BOOTSTRAPS_METTA = "bootstraps.metta"
""" config key for metta bootstraps inside any config block """
METTA_PLUGIN_CONFIG_KEY_ENVIRONMENT_STATES = "states.available"
""" this config key inside an environment config can describe states """
METTA_PLUGIN_CONFIG_KEY_ENVIRONMENT_DEFAULT_STATE = "states.default"
""" this config key inside an environment config that overrides using the first state as default """
METTA_PLUGIN_CONFIG_KEY_FROM_CONFIG = "from_config"
""" config key that indicates that the plugin will be build from aconfig label/key pair """

METTA_ENVIRONMENT_STATE_UNUSED_NAME = "default"
""" what an environment will use for state name if no states are used in the environment """

DEFAULT_SOURCE_PRIORITY = 40
""" If the environment constructor finds config sources to add, this is their default priority """


# pylint: disable=R0902
class Environment:
    """A testing environment, usually composed of a config and plugins."""

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        name: str,
        config: Config,
        bootstraps: List[str] = None,
        config_label: str = "",
        config_base: Union[str, List[Any]] = None,
        default_priority: int = DEFAULT_SOURCE_PRIORITY,
    ):
        """Initialize environment state.

        Parameters:
        -----------
        config (configerus.Config) : A single config object which will be used
            to define the environment.

        bootstraps (List[str]) : a list of metta bootstraps to run. This will be
            combined with a default set, and may also be combined with a set
            from config.

        default_priority (int) : integer values are used to sort created
            fixtures. this value is used in cases where no priority has been
            specified.

        # Config Context : the following parameters will tell the Environment
            object to examine config for additional actions to take.  For
            example additional config source may be added, and fixtures may be
            created.

        Label (str) : Config label to load to find environment config.
        Base (Mixed) : config base key to use to find environment config.  This
            can be either a string or any nested combination of Lists of
            strings, which Configerus joins into a flat list.

        """
        if bootstraps is None:
            bootstraps = []
        if config_base is None:
            config_base = LOADED_KEY_ROOT

        self.name = name
        """ what does the environment call itself """

        # make a copy of the config object as it will likely be shared across contexts
        # that we don't want to have impact this environment obect
        self.config = config.copy()
        """ Config object that defines the environment """
        self.config_backup = config.copy()
        """ Make a dupe of the starting config which we will use whenever we change state """

        # Config label & base are configerus concepts used for loading data:
        # label (str) : can roughly be compared with config file name, without the file suffix
        #     but it will contain merged config from multiple sources.
        # base (str of List of stuff) : directs the path down the loaded config from the label.
        self.config_label: str = config_label
        """ configerus load label """
        self.config_base = config_base
        """ environment config base """

        self.default_priority = int(default_priority)
        """ Default priority int value used for when no priority is assigned """

        self.fixtures = Fixtures()
        """ fixtures/plugins that can interact with the environment """
        self.default_plugin_priority = DEFAULT_PLUGIN_PRIORITY
        """ Default integer priority for new fixtures """

        self.bootstraps = bootstraps
        """ keep the original list of bootstraps to be applied on every state change """
        self.bootstrapped: List[str] = []
        """ list of bootstraps that have already been applied to prevent repetition """

        self.states: List[str] = []
        """ list of allowed states for the environment """
        self.state: str = ""
        """ currently active state for the environment """

        if not self.config_label:
            # this environment does not have a related configuration to program
            # itself with, but it could have had bootstraps.
            logger.info("New environment created: %s (not from config)", name)

            self.bootstrap(bootstraps)
            # this was the original mechanisms for defining environments, and  does have usecases
            # left today for simple environment definition, but any serious environment usage would
            # be much better served by using the configuration options; it lets you define more
            # config sources, fixtures, bootstraps etc.

        else:

            logger.info("New environment created: %s", name)

            # There is a config dict to add to the environment
            config_environment = self.config.load(self.config_label)

            try:
                config_environment.get(self.config_base)
            except ValueError as err:
                raise ValueError("Environment config not found") from err

            # Grab all of the environment state keys/names. Default to an empty
            # list,
            self.states = list(
                config_environment.get(
                    [self.config_base, METTA_PLUGIN_CONFIG_KEY_ENVIRONMENT_STATES],
                    default={},
                ).keys()
            )
            # If this environment doesn't use states then pretend there is a
            # state named after our default value.
            if len(self.states) == 0:
                state = METTA_ENVIRONMENT_STATE_UNUSED_NAME
            else:
                # if there is no config for default state, then None is passed to the state loader
                # which will ignore all state configurations.
                state = config_environment.get(
                    [config_base, METTA_PLUGIN_CONFIG_KEY_ENVIRONMENT_DEFAULT_STATE],
                    default="",
                )
                """ what state should be activated on construction.  Can be empty """

            # We run this function even if we have no state, just so we can put
            # all of the config loading in that loader.
            self.set_state(state)

    def set_state(self, state: str = METTA_ENVIRONMENT_STATE_UNUSED_NAME):
        """Set the enivronment state to one of the options for the state.

        Reload the environment with a new state.  This reloads the entire
        environment, configuring the environment for one of the preconfigured
        states.

        @NOTE When state is set, all fixtures are forgotten from the
            environment, but if you have a fixture in scope and use it, it is
            still aware of its environment and can still cause change in the
            scope.  It is up to the consumer to be aware of this.

        Parameters:
        -----------
        state (str) : string state label, which indicates that configuration
            from that state set should be included.

        @NOTE not all environments have multiple states, but all environments
        will use this method to initialize.  To accomodate this a None state is
        allowed.

        """
        # If we are already in that requested state then back out
        if self.state == state:
            return

        # is the requested state in the list of avialabler states
        if not (state == METTA_ENVIRONMENT_STATE_UNUSED_NAME or state in self.states):
            raise KeyError(
                f"Requested environment state has not been configured: {state}"
            )

        self.state = state
        self.config = self.config_backup.copy()

        self.fixtures = Fixtures()
        """ fixtures/plugins that can interact with the environment """
        self.bootstrapped = []
        """ list of bootstraps that have already been applied to prevent repetition """

        # load config for the environment
        config_environment = self.config.load(self.config_label)

        config_base = self.config_base
        """ common config base for all environment states """

        # here we check if there is a state that should come from config.
        # if the state looks liek a real key then we build a config base for it
        # for loading config from that path, otherwsie we leave it as None
        # which is used for testing later in this method.
        if state in [METTA_ENVIRONMENT_STATE_UNUSED_NAME, state]:
            state_config_base = None
        else:
            state_config_base = [
                config_base,
                METTA_PLUGIN_CONFIG_KEY_ENVIRONMENT_STATES,
                state,
            ]
            """ config base for the selected state """

        # Check for config sources from the environment configuration that is
        # shared across all states
        self._add_config_sources_from_config(
            label=self.config_label, base=[config_base, "config.sources"]
        )
        # check for state configuration sources
        if state_config_base is not None:
            self._add_config_sources_from_config(
                label=self.config_label, base=[state_config_base, "config.sources"]
            )

        # Check to see if we should pass any bootstraps to the env factory.
        bootstraps = self.bootstraps.copy()
        bootstraps += config_environment.get(
            [config_base, METTA_PLUGIN_CONFIG_KEY_BOOTSTRAPS_METTA], default=[]
        )
        if state_config_base is not None:
            # Add any bootstraps declared in the env config
            bootstraps += config_environment.get(
                [state_config_base, METTA_PLUGIN_CONFIG_KEY_BOOTSTRAPS_METTA],
                default=[],
            )

        self.bootstrap(bootstraps)

        # Look for fixture definitions in the environment config.
        #
        # One of two options is available here, either:
        # 1. your environment config has a fixtures dict of fixture definitions, or
        # 2. your environment config has a from_config dict which tells us to look
        #    elsewhere.
        # (the same rules are then applied globally and to the active state)

        # If your environment config has a fixtures definition with from_config
        # then the fixtures will be loaded from a different config source.
        # we will look for config like .fixtures and
        # .fictures.from_config.[label|base]
        if config_environment.has(
            [
                config_base,
                METTA_FIXTURES_CONFIG_FIXTURES_LABEL,
                METTA_PLUGIN_CONFIG_KEY_FROM_CONFIG,
            ]
        ):
            # here is case #2 ^ - we have been told to look elsewhere for fixtures.
            label = config_environment.get(
                [
                    config_base,
                    METTA_FIXTURES_CONFIG_FIXTURES_LABEL,
                    METTA_PLUGIN_CONFIG_KEY_FROM_CONFIG,
                    "label",
                ],
                default=METTA_FIXTURES_CONFIG_FIXTURES_LABEL,
            )
            base = config_environment.get(
                [
                    config_base,
                    METTA_FIXTURES_CONFIG_FIXTURES_LABEL,
                    METTA_PLUGIN_CONFIG_KEY_FROM_CONFIG,
                    "base",
                ],
                default=LOADED_KEY_ROOT,
            )
            self.add_fixtures_from_config(label=label, base=base)
        elif config_environment.has(
            [config_base, METTA_FIXTURES_CONFIG_FIXTURES_LABEL]
        ):
            self.add_fixtures_from_config(
                label=label, base=[config_base, METTA_FIXTURES_CONFIG_FIXTURES_LABEL]
            )

        if state_config_base is not None:
            # if your state definition has a fixtures "from_config" section,
            # then it will be loaded from a different config source as describe
            # using a label/base pair
            if config_environment.has(
                [
                    state_config_base,
                    METTA_FIXTURES_CONFIG_FIXTURES_LABEL,
                    METTA_PLUGIN_CONFIG_KEY_FROM_CONFIG,
                ]
            ):
                label = config_environment.get(
                    [
                        state_config_base,
                        METTA_FIXTURES_CONFIG_FIXTURES_LABEL,
                        METTA_PLUGIN_CONFIG_KEY_FROM_CONFIG,
                        "label",
                    ],
                    default=METTA_FIXTURES_CONFIG_FIXTURES_LABEL,
                )
                base = config_environment.get(
                    [
                        state_config_base,
                        METTA_FIXTURES_CONFIG_FIXTURES_LABEL,
                        METTA_PLUGIN_CONFIG_KEY_FROM_CONFIG,
                        "base",
                    ],
                    default=LOADED_KEY_ROOT,
                )
                self.add_fixtures_from_config(label=label, base=base)

            # If you state config has inline fixtures then they are added.
            elif config_environment.has(
                [state_config_base, METTA_FIXTURES_CONFIG_FIXTURES_LABEL]
            ):
                self.add_fixtures_from_config(
                    label=label,
                    base=[config_base, METTA_FIXTURES_CONFIG_FIXTURES_LABEL],
                )

    def _add_config_sources_from_config(self, label: str, base: Union[str, List[Any]]):
        """Ddd more config sources based on in config settings.

        Read some config which will tell us where more config can be found.
        This lets us use config to extend config, and is what make metta
        entirely extensible from a single metta.yml file.

        In the trade-off battle between configurable and convention, this leans
        heavily towards configuration, but it easily lends to standards.

        Parameters:
        -----------
        label (str) : configurus load label.
        base (str|List[str]) : configerus get key as a base for retrieving all
            config settings.

        """
        config_environment = self.config.load(label)
        config_sources = config_environment.get(base, default={})

        for instance_id in config_sources.keys():
            instance_base = [base, instance_id]

            # Keep in mind that the following plugin metadata is about
            # configerus plugins, not metta plugins.

            plugin_id = config_environment.get([instance_base, "plugin_id"])
            priority = config_environment.get(
                [instance_base, "priority"], default=DEFAULT_SOURCE_PRIORITY
            )

            logger.debug(
                "Adding metta sourced config plugin to '%s' environment: %s:%s",
                self.name,
                plugin_id,
                instance_id,
            )
            plugin = self.config.add_source(
                plugin_id=plugin_id, instance_id=instance_id, priority=priority
            )

            # Configerus plugins all work differently so we take a different
            # approach per plugin
            if plugin_id == PLUGIN_ID_SOURCE_PATH:
                path = config_environment.get([instance_base, CONFIGERUS_PATH_KEY])
                plugin.set_path(path=path)
            elif plugin_id == PLUGIN_ID_SOURCE_DICT:
                data = config_environment.get([instance_base, CONFIGERUS_DICT_DATA_KEY])
                plugin.set_data(data=data)
            elif plugin_id == PLUGIN_ID_SOURCE_ENV_SPECIFIC:
                source_base = config_environment.get(
                    [instance_base, CONFIGERUS_ENV_SPECIFIC_BASE_KEY]
                )
                plugin.set_base(base=source_base)
            elif plugin_id == PLUGIN_ID_SOURCE_ENV_JSON:
                source_env = config_environment.get(
                    [instance_base, CONFIGERUS_ENV_JSON_ENV_KEY]
                )
                plugin.set_env(env=source_env)
            # this should probably be a configerus standard
            elif hasattr(plugin, "set_data"):
                data = config_environment.get([instance_base, "data"])
                plugin.set_data(data=data)
            else:
                logger.warning(
                    "had no way of configuring new Configerus source plugin %s",
                    plugin_id,
                )

    def bootstrap(self, entrypoints: List[str]):
        """Bootstrap some METTA distributions.

        METTA bootstrapping is an attempt to allow an easy in to including
        contrib functionality without having to do a lot of Python imports.

        BootStrapping is a setuptools enabled process, where any python package
        can declare a bootstraper, and this function will run that bootstrapper
        on request.
        The BootStrap entry_points are expected to receive a config object on
        which they can operate to add any specific or global functionality.

        BootStraps are typically used for two behaviours:

        1. just import files which run configerus or metta decorators to register
            plugins
        2. add source/formatter/validator plugins to the passed config object.

        Parameters:
        -----------
        bootstrap (List[str]) : a list of string bootstrapper entry_points for
            the ucct.bootstrap entry_points (part of setuptools.)
            Each value needs to refer to a valid entrypoint which will be
            executed with the config object as an argument.

        Raises:
        -------
        Raises a KeyError in cases of a bootstrap ID that cannot be found.

        Bootstrappers themselves may raise an exception.

        """
        for entrypoint in entrypoints:
            if entrypoint not in self.bootstrapped:
                logger.debug("Running metta bootstrap entrypoint: %s ", entrypoint)
                for metta_ep in metadata.entry_points()[METTA_BOOTSTRAP_ENTRYPOINT]:
                    if metta_ep.name == entrypoint:
                        plugin = metta_ep.load()
                        plugin(self)
                        self.bootstrapped.append(entrypoint)
                        break
                else:
                    raise KeyError(
                        f"Bootstrap not found {METTA_BOOTSTRAP_ENTRYPOINT}:{entrypoint}"
                    )
            else:
                logger.debug(
                    "Skipping boostrap %s, as it has already been imported", entrypoint
                )

    def plugin_priority(self, delta: int = 0):
        """Return a default plugin priority with a delta."""
        return self.default_priority + delta

    # Generic Plugin construction

    def add_fixtures_from_config(
        self,
        label: str = METTA_FIXTURES_CONFIG_FIXTURES_LABEL,
        base: Union[str, List[Any]] = LOADED_KEY_ROOT,
        validator: str = "",
        exception_if_missing: bool = False,
        arguments: Dict[str, Any] = None,
    ) -> Fixtures:
        """Create plugin fixtures from some config.

        This method will interpret some config values as being usable to build a
        collection of plugins from.  The plugins will be built, wrapped as
        fixtures and added to the Environment.  The plugins will then be
        returned as a Fixtures collection.

        Parameters:
        -----------
        config (Config) : Used to load and get the plugin configuration

        label (str) : config label to load to pull plugin configuration. That
            label is loaded and config is pulled to produce a list of plugins

        base (str|List) : config key to get Dict of plugins configurations. This
            should point to a dict of plugin configurations.
            A list of strings is valid as configerus.loaded.get() can take that
            as an argument.
            We call this base instead of key as we will be searching for
            sub-paths to pull individual elements

        validator (str) : optionally use a configerus validator on the instance
            config/dict before a plugin is created.

        arguments (Dict[str, Any]) : A Dict of named arguments to pass to the
            plugin constructor.  Constructors should be able to work without
            requiring the arguments, but these tend to be pivotal for them.

        Returns:
        --------
        Fixtures set as directed by the passed config.

        Raises:
        -------
        If you ask for a plugin which has not been registered, then you're going
        to get a NotImplementedError exception.
        To make sure that your desired plugin is registered, make sure to import
        the module that contains the factory method with a decorator.

        """
        if arguments is None:
            arguments = {}

        fixtures = Fixtures()
        """ plugin set which will be used to create new plugins """

        try:
            plugin_config = self.config.load(label)
            plugin_list = plugin_config.get(base)
        except KeyError as err:
            if exception_if_missing:
                raise KeyError(
                    "Could not load any config for plugin generation"
                ) from err
            return fixtures

        for instance_id in plugin_list.keys():
            # This fixture gets effectively added to 2 different Fixtures object.
            # 1. we manually add it to our Fixtures object for this function call
            # 2. the add_fixture_from_config() adds it to the fixture for this
            #    environment object.
            fixture = self.add_fixture_from_config(
                label=label,
                base=[base, instance_id],
                instance_id=instance_id,
                validator=validator,
                arguments=arguments,
            )
            fixtures.add(fixture)

        return fixtures

    def add_fixture_from_config(
        self,
        label: str,
        base: Union[str, List[Any]] = LOADED_KEY_ROOT,
        instance_id: str = "",
        priority: int = -1,
        validator: str = "",
        arguments: Dict[str, Any] = None,
    ) -> Fixture:
        """Create and add a new plugin fixture from some config.

        This method will interpret some config values as being usable to build a
        single plugin.  The plugin will be built, wrapped as a Fixture, and
        added to the environment. The plugin Fixture is returned.

        @see add_fixture_from_loadedconfig

        @note we could validate here instead of passing on the validator, but we
            pass it on to keep parity across a number of cases, and to keep as
            much complex logic in one place.

        Parameters:
        -----------
        config (Config) : Used to load and get the plugin configuration

        label (str) : config label to load to pull plugin configuration. That
            label is loaded and config is pulled to produce a list of plugins.

        base (str|List) : config key used as a .get() base for all gets.  With
            this you can instruct to pull config from a section of loaded
            config.
            A list of strings is valid because configerus.loaded.get() can take
            that as an argument. We will be using the list syntax anyway. We
            call this base instead of key as we will be searching for  sub-paths
            to pull individual elements.

        instance_id (str) : optionally pass an instance_id for the item.

        validator (str) : optionally use a configerus validator on the entire
            .get() for the instance config.

        Returns:
        --------
        A Fixture object that wraps the created plugin.

        The Fixtures has already been added to the environment, but is returned
        so that the consumer can act on it separately without haveing to
        search for it.

        Raises:
        -------
        If you ask for a plugin which has not been registered, then you're going
        to get a NotImplementedError exception. To make sure that your desired
        plugin is registered, make sure to import the module that contains the
        factory method with a decorator.

        A ValueError is thrown if the plugin cannot be created due to missing
        plugin configuration/argument values.  This means that we could not
        determine how to create the plugin.

        A configerus.validate.ValidationError will be raised if a validation
        target was passed and validation failed.

        """
        if arguments is None:
            arguments = {}

        try:
            plugin_loaded = self.config.load(label)
            """ loaded configuration for the plugin """
        except KeyError as err:
            raise KeyError(f"Could not load plugin config source {label}") from err

        # If arguments were given then pass them on
        try:
            config_arguments = plugin_loaded.get(
                [base, METTA_PLUGIN_CONFIG_KEY_ARGUMENTS]
            )
            config_arguments.update(arguments)
            arguments = config_arguments
        except KeyError:
            if not arguments:
                # if no arguments were specified, then consider a special case of
                # 'from_config' which build arguments for a config based plugin
                # which will take a config label/base-key pair as config arguments
                #
                # There is a special case where if the passed from_config is not a
                # dict then the same config label/base received is used.
                try:
                    config_fromconfig = plugin_loaded.get(
                        [base, METTA_PLUGIN_CONFIG_KEY_FROM_CONFIG]
                    )

                    if isinstance(config_fromconfig, dict):
                        logger.debug(
                            "Using from_config, and passing label/base as arguments"
                        )
                        arguments = config_fromconfig
                    else:
                        logger.debug(
                            "Using from_config, and passing current label/base as arguments"
                        )
                        arguments = {"label": label, "base": base}
                except KeyError:
                    pass

        return self.add_fixture_from_loadedconfig(
            loaded=plugin_loaded,
            base=base,
            instance_id=instance_id,
            priority=priority,
            validator=validator,
            arguments=arguments,
        )

    def add_fixture_from_dict(
        self,
        plugin_dict: Dict[str, Any],
        instance_id: str = "",
        validator: str = "",
        arguments: Dict[str, Any] = None,
    ) -> Fixture:
        """Create a single plugin from a Dict of information for it.

        Create a new plugin from a map/dict of settings for needed parameters.

        @see add_fixture_from_loadedconfig

        Parameters:
        -----------
        config (Config) : configerus.Config object passed to each generated plugins.

        client_dict (Dict[str,Any]) : Dict from which all needed information will
            be pulled.  Optionally additional config sources can be included as
            well as arguments which could be passed to the plugin.

            @see add_fixture_from_dict for more details.

        instance_id (str) : optionally pass an instance_id for the item.

        validator (str) : optionally use a configerus validator on the entire
            .get() for the instance config.

        Return:
        -------
        A Fixture object with the new plugin added

        The Fixtures has already been added to the environment, but is returned
        so that the consumer can act on it separately without haveing to
        search for it.

        """
        # Create a mock configerus.loaded.Loaded object, not attached to anything
        # and use it for config retrieval.  This gives us formatting, validation
        # etc.
        mock_config_loaded = Loaded(
            data=plugin_dict, parent=self.config, instance_id="mock-plugin-construct"
        )
        """ Mock configerus loaded object for config retrieval """
        base = LOADED_KEY_ROOT
        """ keep similar to add_fixture_from_config we use an empty .get() base """

        if arguments is None:
            arguments = {}

        return self.add_fixture_from_loadedconfig(
            loaded=mock_config_loaded,
            base=base,
            instance_id=instance_id,
            validator=validator,
            arguments=arguments,
        )

    # This is where we centralize all logic around creating fixtures, so it is complex
    # pylint: disable=too-many-branches, too-many-locals
    def add_fixture_from_loadedconfig(
        self,
        loaded: Loaded,
        base: Union[str, List[Any]] = LOADED_KEY_ROOT,
        instance_id: str = "",
        priority: int = -1,
        validator: str = "",
        arguments: Dict[str, Any] = None,
    ) -> Fixture:
        """Create a plugin from a Configerus loaded config object.

        This method will interpret some config values as being usable to build
        plugin. This function starts with a loaded config object because we can
        leverage that from more starting points.

        Using a configerus config object allows us to leverage advanced
        configerus features such as tree searching, formatting and validation.

        What is looked for:

        1. valdiators if we need to validate the entire label/key before using
        2. plugin_id : which will tell us what plugin to load
        3. optional instance_id if none was passed
        4. config if you want config added - ONLY if fixtures is None
           (plugins in Fixtures cannot override config objects)
        5. arguments that will be executed on an argument() method if the
            plugin has it.

        @TODO we should probably allow a setting to allow replacing existing
            fixtures in the environment.

        Parameters:
        -----------
        config (Config) : Used to load and get the plugin configuration

        label (str) : config label to load to pull plugin configuration. That
            label is loaded and config is pulled to produce a list of plugins.

        base (str|List) : config key used as a .get() base for all gets.  With
            this you can instruct to pull config from a section of loaded
            config.
            A list of strings is valid because configerus.loaded.get() can take
            that as an argument. We will be using the list syntax anyway.
            We call this base instead of key as we will be searching for
            sub-paths to pull individual elements.

        instance_id (str) : optionally pass an instance_id for the item.

        validator (str) : optionally use a configerus validator on the entire
            .get() for the instance config.

        Returns:
        --------
        A Fixture object with the new plugin added

        The Fixtures has already been added to the environment, but is returned
        so that the consumer can act on it separately without haveing to
        search for it.

        Raises:
        -------
        If you ask for a plugin which has not been registered, then you're going
        to get a NotImplementedError exception. To make sure that your desired
        plugin is registered, make sure to import the module that contains the
        factory method with a decorator.

        A ValueError is thrown if the plugin cannot be created due to missing
        plugin configuration/argument values.  This means that we could not
        determine how to create the plugin.

        A configerus.validate.ValidationError will be raised if a validation
        target was passed and validation failed.

        """
        # Retrieve all of the plugin config, to test that it exists
        # it might be expensive to retrieve all this but we do it to catch early
        # faults in config.
        plugin_base = loaded.get(base)
        """ configuration base object for the plugin """
        if plugin_base is None:
            raise ValueError("Cannot build plugin as provided config was empty.")

        # get any validators from config, defaulting to just the jsonschema
        # validator for a fixture
        validators = loaded.get(
            [base, METTA_FIXTURE_VALIDATION_JSONSCHEMA],
            default=[
                {PLUGIN_ID_VALIDATE_JSONSCHEMA: METTA_FIXTURE_VALIDATION_JSONSCHEMA}
            ],
        )

        if validator:
            # if a validator arg was passed in, then add it
            validators.append(validator)
        if len(validators):
            # Run configerus validation on the config base once per validator
            try:
                for val in validators:
                    loaded.validate(plugin_base, validate_target=val)
            except ValidationError as err:
                raise err

        try:
            plugin_id = str(loaded.get([base, METTA_PLUGIN_CONFIG_KEY_PLUGINID]))
        except KeyError as err:
            full_config = loaded.get(base)
            raise ValueError(
                "Could not find a plugin_id when trying to create a "
                f"plugin from config: {full_config}"
            ) from err

        # if no instance_id was passed, try to load one or just make one up
        if not instance_id:
            instance_id = str(
                loaded.get([base, METTA_PLUGIN_CONFIG_KEY_INSTANCEID], default="")
            )
            if not instance_id:
                instance_rand = "".join(
                    random.choice(string.ascii_lowercase) for i in range(10)
                )
                instance_id = f"{plugin_id}-{instance_rand}"

        if priority < 0:
            priority = int(
                loaded.get(
                    [base, METTA_FIXTURE_CONFIG_KEY_PRIORITY],
                    default=self.plugin_priority(),
                )
            )
            """ instance priority - this is actually a stupid way to get it """

        config_arguments = loaded.get(
            [base, METTA_PLUGIN_CONFIG_KEY_ARGUMENTS], default={}
        )
        if len(config_arguments) > 0:
            if arguments is None:
                arguments = {}
            else:
                # if we have config arguments from two different sources, then
                # add the config args to a copy of the function parameter args.
                # We use a copy so that we make no context mistakes by altering
                # a passed Dict that may get used for more than one plugin.
                arguments = arguments.copy()

            arguments.update(config_arguments)

        # Use the factory to make the .fixtures.Fixture
        fixture = self.add_fixture(
            plugin_id=plugin_id,
            instance_id=instance_id,
            priority=priority,
            arguments=arguments,
        )

        return fixture

    def add_fixture(
        self,
        plugin_id: str,
        instance_id: str,
        priority: int,
        arguments: Dict[str, Any] = None,
        replace_existing=False,
    ) -> Fixture:
        """Create a new plugin from parameters.

        Parameters:
        -----------
        config (Config) : configerus.Config passed to each generated plugins.

        plugin_id (str) : METTA plugin id to tell us what plugin factory to use.

            @see .plugin.Factory for more details on how plugins are loaded.

        instance_id (str) : string instance id that will be passed to the new
            plugin object.

        priority (int) : Integer priority 1-100 for comparative prioritization
            between other plugins.

        arguments (Dict[str, Any]) : Keyword Arguments which should be passed to
            the plugin constructor after environment and instance_id

        replace_existing (bool) : Replace any existing matching fixture.

        Return:
        -------
        A Fixture object with the new plugin added

        The Fixtures has already been added to the environment, but is returned
        so that the consumer can act on it separately without haveing to
        search for it.

        Raises:
        -------
        NotImplementedError if you asked for an unregistered plugin_id

        """
        if arguments is None:
            arguments = {}

        if not (
            isinstance(plugin_id, str)
            and isinstance(instance_id, str)
            and isinstance(priority, int)
        ):
            raise ValueError(
                f"Bad arguments passed for creating a fixture: "
                f":{plugin_id}:{instance_id} ({priority})"
            )

        plugin_instance = Factory.create(
            plugin_id, instance_id, *[self, instance_id], **arguments
        )
        fixture = self.fixtures.add(
            fixture=Fixture.from_instance(plugin_instance, priority=priority),
            replace_existing=replace_existing,
        )
        return fixture
