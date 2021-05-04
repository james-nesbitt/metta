"""

An environment is meant to represent a testable cluster as a testing harness

In METTA an environment is a single configerus Config object and a set of
METTA plugins in a manageable set.

METTA uses the Fixtures object to manage a set of plugins, which allows us to
mix a bunch of plugin objects of different types together and manage them.

@NOTE states were just recently added and are currently inelegant and inefficient
  but should get a refactor soon.

"""
import logging
import random
import string
from typing import List, Dict, Any
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
    CONFIGERUS_ENV_JSON_ENV_KEY)

from .plugin import (
    Factory,
    Type,
    METTAPlugin,
    METTA_PLUGIN_CONFIG_KEY_TYPE,
    METTA_PLUGIN_CONFIG_KEY_PLUGINID,
    METTA_PLUGIN_CONFIG_KEY_INSTANCEID,
    METTA_PLUGIN_CONFIG_KEY_ARGUMENTS,
    METTA_PLUGIN_CONFIG_KEY_PRIORITY,
    METTA_PLUGIN_CONFIG_KEY_CONFIG,
    METTA_PLUGIN_CONFIG_KEY_VALIDATORS)
from .fixtures import (
    Fixtures,
    Fixture,
    METTA_FIXTURES_CONFIG_FIXTURE_KEY,
    METTA_FIXTURES_CONFIG_FIXTURES_LABEL,
    METTA_FIXTURE_VALIDATION_JSONSCHEMA)


import logging

logger = logging.getLogger('metta.environment')

DEFAULT_PLUGIN_PRIORITY = 70
""" Default plugin priority when turned into a fixture """

FIXTURE_VALIDATION_TARGET_FORMAT_STRING = 'jsonschema:{key}'
""" python string .format template for string jsonchema configerus formatter definition """

METTA_BOOTSTRAP_ENTRYPOINT = 'metta.bootstrap'
""" SetupTools entry_point used for METTA bootstrap """

METTA_PLUGIN_CONFIG_LABEL_ENVIRONMENTS = 'environments'
""" config label discover a list of environments in a loaded config """
METTA_PLUGIN_CONFIG_KEY_ENVIRONMENTS = 'environments'
""" this key could be used to discover a list of environments in a loaded config """
METTA_PLUGIN_CONFIG_KEY_BOOTSTRAPS_METTA = 'bootstraps.metta'
""" config key for metta bootstraps inside any config block """
METTA_PLUGIN_CONFIG_KEY_ENVIRONMENT_STATES = 'states.available'
""" this config key inside an environment config can describe states """
METTA_PLUGIN_CONFIG_KEY_ENVIRONMENT_DEFAULT_STATE = 'states.default'
""" this config key inside an environment config that can indicates overrides using the first state as a default """
METTA_PLUGIN_CONFIG_KEY_FROM_CONFIG = 'from_config'
""" config key that indicates that the plugin will be build from aconfig label/key pair """

METTA_ENVIRONMENT_STATE_UNUSED_NAME = 'default'
""" what an environment will use for state name if no states are used in the environment """

DEFAULT_SOURCE_PRIORITY = 40
""" If the environment constructor finds config sources to add, this is their default priority """


class Environment:
    """ A testing environment, usually composed of a config and plugins """

    def __init__(self, name: str, config: Config, bootstraps: List[str] = [
    ], config_label: str = '', config_base: str = LOADED_KEY_ROOT):
        """

        Parameters:
        -----------

        config (configerus.Config) : A single config object which will be used
            to define the environment.

        bootstraps (List[str]) : a list of metta bootstraps to run. This will be
            combined with a default set, and may also be combined with a set
            from config.

        # Config Context : the following two parameters will tell the Environment
            object to examine config for additional actions to take.  For example
            additional config source may be added, and fixtures may be created.

        Label (str) : Config label to load to find environment config.

        Base (str) : config base key to use to find environment config.

        """

        self.name = name
        """ what does the environment call itself """

        # make a copy of the config object as it will likely be shared across contexts
        # that we don't want to have impact this environment obect
        self.config = config.copy()
        """ Config object that defines the environment """
        self.config_backup = config.copy()
        """ Make a dupe of the starting config which we will use whenever we change state """

        self.config_label = config_label
        self.config_base = config_base
        """ environment config label/key pair.  Not always passed, but if it is this
            can play a role in extensible environment configuration """

        self.fixtures = Fixtures()
        """ fixtures/plugins that can interact with the environment """
        self.default_plugin_priority = DEFAULT_PLUGIN_PRIORITY
        """ Default integer priority for new fixtures """

        self.bootstraps = bootstraps
        """ keep the original list of bootstraps to be applied on every state change """
        self.bootstrapped = []
        """ list of bootstraps that have already been applied to prevent repetition """

        self.states = []
        """ list of allowed states for the environment """
        self.state = None
        """ currently active state for the environment """

        if not self.config_label:
            # this environment does not have a related configuration to program
            # itself with, but it could have had bootstraps.

            logger.info(
                "New environment created: {} (not from config)".format(name))

            self.bootstrap(bootstraps)

            # this was the original mechanisms for defining environments, and
            # does have usecases left today for simple environment definition,
            # but any serious environment usage would be much better served by
            # using the configuration options; it lets you define more config
            # sources, fixtures, bootstraps etc.

        else:

            logger.info(
                "New environment created: {} ({}:{})".format(
                    name,
                    self.config_label,
                    self.config_base))

            # There is a config dict to add to the environment
            config_environment = self.config.load(self.config_label)

            try:
                config_environment.get(self.config_base)
            except ValueError:
                raise ValueError(
                    "Environment config didn't contain described label/key: {}:{}".format(label, base))

            # Grab all of the environment state keys/names. Default to an empty
            # list,
            self.states = list(config_environment.get(
                [self.config_base, METTA_PLUGIN_CONFIG_KEY_ENVIRONMENT_STATES], default={}).keys())
            # If this environment doesn't use states then pretend there is a
            # state named after our default value.
            if len(self.states) == 0:
                state = METTA_ENVIRONMENT_STATE_UNUSED_NAME
            else:
                # if there is no config for default state, then None is passed to the state loader
                # which will ignore all state configurations.
                state = config_environment.get(
                    [config_base, METTA_PLUGIN_CONFIG_KEY_ENVIRONMENT_DEFAULT_STATE], default='')
                """ what state should be activated on construction.  Can be empty, which indicates no state """

            # We run this function even if we have no state, just so we can put
            # all of the config loading in that loader.
            self.set_state(state)

    def set_state(self, state: str = METTA_ENVIRONMENT_STATE_UNUSED_NAME):
        """ set the enivronment state to one of the options for the state

        Reload the environment with a new state.  This reloads the entire
        environment, configuring the environment for one of the preconfigured
        states.

        @NOTE When state is set, all fixtures are forgotten from the environment,
        but if you have a fixture in scope and use it, it is still aware of its
        environment and can still cause change in the scope.  It is up to the
        consumer to be aware of this.

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
                "Requested environment state has not been configured: {}".format(state))

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
        if state == METTA_ENVIRONMENT_STATE_UNUSED_NAME or state == '':
            state_config_base = None
        else:
            state_config_base = [
                config_base,
                METTA_PLUGIN_CONFIG_KEY_ENVIRONMENT_STATES,
                state]
            """ config base for the selected state """

        # Check for config sources from the environment configuration that is
        # shared across all states
        self._add_config_sources_from_config(
            label=self.config_label, base=[
                config_base, 'config.sources'])
        # check for state configuration sources
        if state_config_base is not None:
            self._add_config_sources_from_config(
                label=self.config_label, base=[
                    state_config_base, 'config.sources'])

        # Check to see if we should pass any bootstraps to the env factory.
        bootstraps = self.bootstraps.copy()
        bootstraps += config_environment.get(
            [config_base, METTA_PLUGIN_CONFIG_KEY_BOOTSTRAPS_METTA], default=[])
        if state_config_base is not None:
            # Add any bootstraps declared in the env config
            bootstraps += config_environment.get(
                [state_config_base, METTA_PLUGIN_CONFIG_KEY_BOOTSTRAPS_METTA], default=[])

        self.bootstrap(bootstraps)

        # Look for fixture definitions in the environment config.
        #
        # One of two options is available here, either:
        # 1. your config has a fixtures dict of fixture definitions, or
        # 2. you fixtures config has a from_config dict which tells us to look
        # elsewhere
        # (the same rules are then applied to the active state)

        # If your environment config has a fixtures definition with from_config
        # then the fixtures will be loaded from a different config source.
        # we will look for config like .fixtures and
        # .fictures.from_config.[label|base]
        if config_environment.has(
                [config_base, METTA_FIXTURES_CONFIG_FIXTURES_LABEL, METTA_PLUGIN_CONFIG_KEY_FROM_CONFIG]):
            label = config_environment.get([config_base,
                                            METTA_FIXTURES_CONFIG_FIXTURES_LABEL,
                                            METTA_PLUGIN_CONFIG_KEY_FROM_CONFIG,
                                            'label'],
                                           default=METTA_FIXTURES_CONFIG_FIXTURES_LABEL)
            base = config_environment.get([config_base,
                                           METTA_FIXTURES_CONFIG_FIXTURES_LABEL,
                                           METTA_PLUGIN_CONFIG_KEY_FROM_CONFIG,
                                           'base'],
                                          default=LOADED_KEY_ROOT)
            self.add_fixtures_from_config(label=label, base=base)
        elif config_environment.has([config_base, METTA_FIXTURES_CONFIG_FIXTURES_LABEL]):
            self.add_fixtures_from_config(
                label=label, base=[config_base, METTA_FIXTURES_CONFIG_FIXTURES_LABEL])

        if state_config_base is not None:
            # if your state definition has a fixtures "from_config" section,
            # then it will be loaded from a different config source as describe
            # using a label/base pair
            if config_environment.has(
                    [state_config_base, METTA_FIXTURES_CONFIG_FIXTURES_LABEL, METTA_PLUGIN_CONFIG_KEY_FROM_CONFIG]):
                label = config_environment.get(
                    [state_config_base,
                     METTA_FIXTURES_CONFIG_FIXTURES_LABEL,
                     METTA_PLUGIN_CONFIG_KEY_FROM_CONFIG,
                     'label'],
                    default=METTA_FIXTURES_CONFIG_FIXTURES_LABEL)
                base = config_environment.get(
                    [state_config_base,
                     METTA_FIXTURES_CONFIG_FIXTURES_LABEL,
                     METTA_PLUGIN_CONFIG_KEY_FROM_CONFIG,
                     'base'],
                    default=LOADED_KEY_ROOT)
                self.add_fixtures_from_config(label=label, base=base)

            # If you state config has inline fixtures then they are added.
            elif config_environment.has([state_config_base, METTA_FIXTURES_CONFIG_FIXTURES_LABEL]):
                self.add_fixtures_from_config(
                    label=label, base=[
                        config_base, METTA_FIXTURES_CONFIG_FIXTURES_LABEL])

    def _add_config_sources_from_config(self, label, base):
        """ add more config sources based on in config settings """
        config_environment = self.config.load(label)
        config_sources = config_environment.get(base, default={})

        for instance_id in config_sources.keys():
            instance_base = [base, instance_id]

            # Keep in mind that the following plugin metadata is about
            # configerus plugins, not metta plugins.

            plugin_id = config_environment.get([instance_base, 'plugin_id'])
            priority = config_environment.get(
                [instance_base, 'priority'], default=DEFAULT_SOURCE_PRIORITY)

            logger.debug(
                "Adding metta sourced config plugin to '{}' environment: {}:{}".format(self.name, plugin_id, instance_id))
            plugin = self.config.add_source(
                plugin_id=plugin_id, instance_id=instance_id, priority=priority)

            # Configerus plugins all work differently so we take a different
            # approach per plugin
            if plugin_id == PLUGIN_ID_SOURCE_PATH:
                path = config_environment.get(
                    [instance_base, CONFIGERUS_PATH_KEY])
                plugin.set_path(path=path)
            elif plugin_id == PLUGIN_ID_SOURCE_DICT:
                data = config_environment.get(
                    [instance_base, CONFIGERUS_DICT_DATA_KEY])
                plugin.set_data(data=data)
            elif plugin_id == PLUGIN_ID_SOURCE_ENV_SPECIFIC:
                source_base = config_environment.get(
                    [instance_base, CONFIGERUS_ENV_SPECIFIC_BASE_KEY])
                plugin.set_base(base=source_base)
            elif plugin_id == PLUGIN_ID_SOURCE_ENV_JSON:
                source_env = config_environment.get(
                    [instance_base, CONFIGERUS_ENV_JSON_ENV_KEY])
                plugin.set_env(env=source_env)
            elif hasattr(plugin, set_data):
                data = config_environment.get([instance_base, 'data'])
                plugin.set_data(data=data)
            else:
                logger.warn(
                    "had no way of configuring new Configerus source plugin {}".format(plugin_id))

    def bootstrap(self, entrypoints: List[str] = []):
        """ BootStrap some METTA distributions

        METTA bootstrapping is an attempt to allow an easy in to including contrib
        functionality without having to do a lot of Python imports.

        BootStrapping is a setuptools enabled process, where any python package can
        declare a bootstraper, and this function will run that bootstrapper on
        request.
        The BootStrap entry_points are expected to receive a config object on which
        they can operate to add any specific or global functionality.

        BootStraps are typically used for two behaviours:

        1. just import files which run configerus or metta decorators to register
            plugins
        2. add source/formatter/validator plugins to the passed config object.

        Parameters:
        -----------

        bootstrap (List[str]) : a list of string bootstrapper entry_points for the
            ucct.bootstrap entry_points (part of setuptools.)
            Each value needs to refer to a valid entrypoint which will be executed
            with the config object as an argument.

        Raises:
        -------

        Raises a KeyError in cases of a bootstrap ID that cannot be found.

        Bootstrappers themselves may raise an exception.

        """
        for entrypoint in entrypoints:
            if entrypoint not in self.bootstrapped:
                logger.info(
                    "Running metta bootstrap entrypoint: %s",
                    entrypoint)
                eps = metadata.entry_points()[METTA_BOOTSTRAP_ENTRYPOINT]
                for ep in eps:
                    if ep.name == entrypoint:
                        plugin = ep.load()
                        plugin(self)
                        self.bootstrapped.append(entrypoint)
                        break
                else:
                    raise KeyError(
                        "Bootstrap not found {}:{}".format(
                            METTA_BOOTSTRAP_ENTRYPOINT,
                            entrypoint))

    def plugin_priority(self, delta: int = 0):
        """ Return a default plugin priority with a delta """
        return DEFAULT_PLUGIN_PRIORITY + delta

    """

    Generic Plugin construction

    """

    def add_fixtures_from_typeconfig(
            self, label: str, base: Any = LOADED_KEY_ROOT, validator: str = '') -> Fixtures:
        """ Create multiple different fixtures from a structured config source

        This approach to creating fixtures keeps a tree:

        {type}:
            {instance_id}:
                ... {instance config} ...

        Parameters:
        -----------

        config (Config) : Used to load and get the plugin configuration

        label (str) : config label to load to pull plugin configuration. That
            label is loaded and config is pulled to produce a list of plugins

        base (str|List) : config key to get a Dict of plugins configurations.  This
            should point to a dict of plugin configurations.
            A list of strings is valid as configerus.loaded.get() can take that as
            an argument.
            We call this base instead of key as we will be searching for sub-paths
            to pull individual elements

        validator (str) : optionally use a configerus validator on the instance
            config/dict before a plugin is created.

        arguments (Dict[str, Any]) : A Dict of named arguments to pass to the
            plugin constructor.  Constructors should be able to work without
            requiring the arguments, but these tend to be pivotal for them.

        Returns:
        --------

        Fixtures of your type

        Raises:
        -------

        If you ask for a plugin which has not been registered, then you're going to
        get a NotImplementedError exception.
        To make sure that your desired plugin is registered, make sure to import
        the module that contains the factory method with a decorator.

        """
        fixtures = Fixtures()
        """ plugin set which will be used to create new plugins """

        try:
            plugin_config = self.config.load(label)
            plugin_type_list = plugin_config.get(
                base)
        except KeyError as e:
            if exception_if_missing:
                return KeyError(
                    'Could not load any config for plugin generation')
                # there is not config so we can ignore this
            else:
                return fixtures

        # Upper/Outer layer defines plugin type
        for type, plugin_list in plugin_type_list.items():
            # Lower/Inner layer is a list of plugins to create of that type
            for instance_id in plugin_list.keys():
                # This fixture gets effectively added to 2 different Fixtures object.
                # 1. we manually add it to our Fixtures object for this function call
                # 2. the add_fixture_from_config() adds it to the fixture for this
                #    environment object.
                fixture = self.add_fixture_from_config(
                    label=label,
                    base=[base, instance_id],
                    type=type,
                    instance_id=instance_id,
                    validator=validator)
                fixtures.add_fixture(fixture)

        return fixtures

    def add_fixtures_from_config(self, label: str = METTA_FIXTURES_CONFIG_FIXTURES_LABEL, base: Any = LOADED_KEY_ROOT, type: Type = None, validator: str = '',
                                 exception_if_missing: bool = False, arguments: Dict[str, Any] = {}) -> Fixtures:
        """ Create plugins from some config

        This method will interpret some config values as being usable to build a Dict
        of plugins from.

        Parameters:
        -----------

        config (Config) : Used to load and get the plugin configuration

        label (str) : config label to load to pull plugin configuration. That
            label is loaded and config is pulled to produce a list of plugins

        base (str|List) : config key to get a Dict of plugins configurations.  This
            should point to a dict of plugin configurations.
            A list of strings is valid as configerus.loaded.get() can take that as
            an argument.
            We call this base instead of key as we will be searching for sub-paths
            to pull individual elements

        type (.plugin.Type) : plugin type to create, pulled from the config/dict if
            omitted.  If Type is provided by neither argument nor source then
            you're gonna have a bad time.

        validator (str) : optionally use a configerus validator on the instance
            config/dict before a plugin is created.

        arguments (Dict[str, Any]) : A Dict of named arguments to pass to the
            plugin constructor.  Constructors should be able to work without
            requiring the arguments, but these tend to be pivotal for them.

        Returns:
        --------

        Fixtures of your type

        Raises:
        -------

        If you ask for a plugin which has not been registered, then you're going to
        get a NotImplementedError exception.
        To make sure that your desired plugin is registered, make sure to import
        the module that contains the factory method with a decorator.

        """
        fixtures = Fixtures()
        """ plugin set which will be used to create new plugins """

        try:
            plugin_config = self.config.load(label)
            plugin_list = plugin_config.get(base)
        except KeyError as e:
            if exception_if_missing:
                raise KeyError(
                    'Could not load any config for plugin generation') from e
                # there is not config so we can ignore this
            else:
                return fixtures

        for instance_id in plugin_list.keys():
            # This fixture gets effectively added to 2 different Fixtures object.
            # 1. we manually add it to our Fixtures object for this function call
            # 2. the add_fixture_from_config() adds it to the fixture for this
            #    environment object.
            fixture = self.add_fixture_from_config(
                label=label,
                base=[base, instance_id],
                type=type,
                instance_id=instance_id,
                validator=validator,
                arguments=arguments)
            fixtures.add_fixture(fixture)

        return fixtures

    def add_fixtures_from_dict(self, plugin_list: Dict[str, Dict[str, Any]], type: Type = None,
                               validator: str = '', arguments: Dict[str, Any] = {}) -> Fixtures:
        """ Create a set of plugins from Dict information

        The passed dict should be a key=>details map of plugins, which will be turned
        into a Fixtures map of plugins that can be used to interact with the
        objects.

        Parameters:
        -----------

        config (Config) : configerus.Config object passed to each generated plugins.

        type (.plugin.Type) : plugin type to create, pulled from the config/dict if
            omitted

        provisioner_list (Dict[str, Dict]) : map of key=> config dicts, where each dict
            contains all of the information that is needed to build the plugin.

            for details, @see add_fixture_from_dict

        validator (str) : optionally use a configerus validator on the instance
            config/dict before a plugin is created.

        arguments (Dict[str, Any]) : A Dict of named arguments to pass to the
            plugin constructor.  Constructors should be able to work without
            requiring the arguments, but these tend to be pivotal for them.

        Returns:
        --------

        A Fixtures object with the plugin objects created

        """
        fixtures = Fixtures()

        if not isinstance(plugin_list, dict):
            raise ValueError(
                'Did not receive a good dict of config to make plugins from: %s',
                plugin_list)

        for instance_id, plugin_dict in plugin_list.items():
            # This fixture gets effectively added to 2 different Fixtures object.
            # 1. we manually add it to our Fixtures object for this function call
            # 2. the add_fixture_from_config() adds it to the fixture for this
            #    environment object.
            fixture = self.add_fixture_from_dict(
                plugin_dict=plugin_dict,
                type=type,
                instance_id=instance_id,
                validator=validator,
                arguments=arguments)
            fixtures.add_fixture(fixture)

        return fixtures

    def add_fixture_from_config(self, label: str, base: Any = LOADED_KEY_ROOT, type: Type = None,
                                instance_id: str = '', priority: int = -1, validator: str = '', arguments: Dict[str, Any] = {}) -> Fixture:
        """ Create a plugin from some config

        This method will interpret some config values as being usable to build plugin

        @see add_fixture_from_loadedconfig

        @note we could validate here instead of passing on the validator, but we
            pass it on to keep parity across a number of cases, and to keep as
            much complex logic in one place.

        Parameters:
        -----------

        config (Config) : Used to load and get the plugin configuration

        type (.plugin.Type) : plugin type to create, pulled from the config/dict if
            omitted. An exception will be thrown if Type is found from neither
            this argument nor the passed config.

        label (str) : config label to load to pull plugin configuration. That
            label is loaded and config is pulled to produce a list of plugins.

        base (str|List) : config key used as a .get() base for all gets.  With this
            you can instruct to pull config from a section of loaded config.
            A list of strings is valid because configerus.loaded.get() can take that
            as an argument. We will be using the list syntax anyway.
            We call this base instead of key as we will be searching for sub-paths
            to pull individual elements.

        instance_id (str) : optionally pass an instance_id for the item.

        validator (str) : optionally use a configerus validator on the entire .get()
            for the instance config.

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
        try:
            plugin_loaded = self.config.load(label)
        except KeyError as e:
            raise KeyError("Could not load plugin config source.") from e
        """ loaded configuration for the plugin """

        # If arguments were given then pass them on
        try:
            config_arguments = plugin_loaded.get(
                [base, METTA_PLUGIN_CONFIG_KEY_ARGUMENTS])
            config_arguments.update(arguments)
            arguments = config_arguments
        except KeyError as e:
            if not arguments:
                # if no arguments were specified, then consider a special case of
                # 'from_config' which build arguments for a config based plugin
                # which will take a config label/base-key pair as config arguments
                #
                # There is a special case where if the passed from_config is not a
                # dict then the same config label/base received is used.
                try:
                    config_fromconfig = plugin_loaded.get(
                        [base, METTA_PLUGIN_CONFIG_KEY_FROM_CONFIG])

                    if isinstance(config_fromconfig, dict):
                        logger.debug(
                            "Using from_config, and passing label/base as arguments")
                        arguments = config_fromconfig
                    else:
                        logger.debug(
                            "Using from_config, and passing current label/base as arguments")
                        arguments = {
                            'label': label,
                            'base': base
                        }
                except KeyError as e:
                    pass

        return self.add_fixture_from_loadedconfig(loaded=plugin_loaded, base=base, type=type,
                                                  instance_id=instance_id, priority=priority, validator=validator, arguments=arguments)

    def add_fixture_from_dict(self, plugin_dict: Dict[str, Any], type: Type = None,
                              instance_id: str = '', validator: str = '', arguments: Dict[str, Any] = {}) -> Fixture:
        """ Create a single plugin from a Dict of information for it

        Create a new plugin from a map/dict of settings for the needed parameters.

        @see add_fixture_from_loadedconfig

        Parameters:
        -----------

        config (Config) : configerus.Config object passed to each generated plugins.

        type (.plugin.Type) : plugin type to create, pulled from the config/dict if
            omitted

        client_dict (Dict[str,Any]) : Dict from which all needed information will
            be pulled.  Optionally additional config sources can be included as well
            as arguments which could be passed to the plugin.

            @see add_fixture_from_dict for more details.

        instance_id (str) : optionally pass an instance_id for the item.

        validator (str) : optionally use a configerus validator on the entire .get()
            for the instance config.

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
            data=plugin_dict,
            parent=self.config,
            instance_id='mock-plugin-construct')
        """ Mock configerus loaded object for config retrieval """
        base = LOADED_KEY_ROOT
        """ to keep this function similar to add_fixture_from_config we use an empty .get() base """

        return self.add_fixture_from_loadedconfig(
            loaded=mock_config_loaded, base=base, type=type, instance_id=instance_id, validator=validator, arguments=arguments)

    def add_fixture_from_loadedconfig(self, loaded: Loaded, base: Any = LOADED_KEY_ROOT, type: Type = None,
                                      instance_id: str = '', priority: int = -1, validator: str = '', arguments: Dict[str, Any] = {}) -> Fixture:
        """ Create a plugin from loaded config

        This method will interpret some config values as being usable to build plugin.
        This function starts with a loaded config object because we can leverage
        that from more starting points.

        Using a configerus config object allows us to leverage advanced configerus
        features such as tree searching, formatting and validation.

        What is looked for:

        1. valdiators if we need to validate the entire label/key before using it
        2. type if we did not receive a type
        3. plugin_id : which will tell us what plugin to load
        4. optional instance_id if none was passed
        5. config if you want config added - ONLY if fixtures is None
           (plugins in Fixtures cannot override config objects)
        6. arguments that will be executed on an argument() method if the
            plugin has it.

        Parameters:
        -----------

        config (Config) : Used to load and get the plugin configuration

        type (.plugin.Type) : plugin type to create, pulled from the config/dict if
            omitted. An exception will be thrown if Type is found from neither
            this argument nor the passed config.

        label (str) : config label to load to pull plugin configuration. That
            label is loaded and config is pulled to produce a list of plugins.

        base (str|List) : config key used as a .get() base for all gets.  With this
            you can instruct to pull config from a section of loaded config.
            A list of strings is valid because configerus.loaded.get() can take that
            as an argument. We will be using the list syntax anyway.
            We call this base instead of key as we will be searching for sub-paths
            to pull individual elements.

        instance_id (str) : optionally pass an instance_id for the item.

        validator (str) : optionally use a configerus validator on the entire .get()
            for the instance config.

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
        logger.debug(
            'Construct config plugin [{}][{}]'.format(
                type, instance_id))

        # it might be expensive to retrieve all this but we do it to catch early
        # faults in config.
        plugin_base = loaded.get(base)
        if plugin_base is None:
            raise ValueError(
                "Cannot build plugin as provided config was empty.")

        # get any validators from config, defaulting to just the jsonschema
        # validator for a fixture
        validators = loaded.get([base, METTA_PLUGIN_CONFIG_KEY_VALIDATORS], default=[
                                {PLUGIN_ID_VALIDATE_JSONSCHEMA: METTA_FIXTURE_VALIDATION_JSONSCHEMA}])
        if validator:
            # if a validator arg was passed in, then add it
            validators.append(validator)
        if len(validators):
            # Run configerus validation on the config base once per validator
            try:
                for validator in validators:
                    loaded.validate(plugin_base, validate_target=validator)
            except ValidationError as e:
                raise e

        if type is None:
            try:
                type = loaded.get([base, METTA_PLUGIN_CONFIG_KEY_TYPE])
            except KeyError as e:
                raise ValueError(
                    "Could not find a plugin type when trying to create a plugin : {}".format(
                        loaded.get(base))) from e
        if isinstance(type, str):
            # If a string type was passed in, ask the Type enum to convert it
            type = Type.from_string(type)

        try:
            plugin_id = loaded.get([base, METTA_PLUGIN_CONFIG_KEY_PLUGINID])
        except KeyError as e:
            raise ValueError(
                "Could not find a plugin_id when trying to create a '{}' plugin from config: {}".format(
                    type, loaded.get(base))) from e

        # if no instance_id was passed, try to load one or just make one up
        if not instance_id:
            instance_id = loaded.get(
                [base, METTA_PLUGIN_CONFIG_KEY_INSTANCEID], default='')
            if not instance_id:
                instance_id = '{}-{}-{}'.format(type.value, plugin_id, ''.join(
                    random.choice(string.ascii_lowercase) for i in range(10)))

        if priority < 0:
            priority = loaded.get([base,
                                   METTA_PLUGIN_CONFIG_KEY_PRIORITY],
                                  default=self.plugin_priority())
            """ instance priority - this is actually a stupid way to get it """

        # If arguments were given then pass them on
        config_arguments = loaded.get(
            [base, METTA_PLUGIN_CONFIG_KEY_ARGUMENTS], default={})
        if len(config_arguments) > 0:
            arguments = arguments.copy()
            arguments.update(config_arguments)

        # Use the factory to make the .fixtures.Fixture
        fixture = self.add_fixture(
            type=type,
            plugin_id=plugin_id,
            instance_id=instance_id,
            priority=priority,
            arguments=arguments)

        return fixture

    def add_fixture(self, type: Type, plugin_id: str,
                    instance_id: str, priority: int, arguments: Dict[str, Any] = {}) -> Fixture:
        """ Create a new plugin from parameters

        Parameters:
        -----------

        config (Config) : configerus.Config object passed to each generated plugins.

        type (.plugin.Type) : plugin type to create.

        plugin_id (str) : METTA plugin id for the plugin type, to tell us what plugin
            factory to load.

            @see .plugin.Factory for more details on how plugins are loaded.

        instance_id (str) : string instance id that will be passed to the new plugin
            object.

        priority (int) : Integer priority 1-100 for comparative prioritization
            between other plugins.

        arguments (Dict[str, Any]) : Arguments which should be passed to the
            plugin constructor after environment and instance_id

        Return:
        -------

        A Fixture object with the new plugin added

        The Fixtures has already been added to the environment, but is returned
        so that the consumer can act on it separately without haveing to
        search for it.

        Raises:
        -------

        NotImplementedError if you asked for an unregistered plugin_id/type

        """
        fac = Factory(type, plugin_id)
        plugin = fac.create(self, instance_id, **arguments)
        fixture = self.fixtures.new_fixture(
            plugin=plugin,
            type=type,
            plugin_id=plugin_id,
            instance_id=instance_id,
            priority=priority)
        return fixture
