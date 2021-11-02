"""

Utility mixins for Environment objects.

"""
from logging import getLogger
from typing import List, Dict, Any, Callable, Optional, Union
import random
import string

from configerus.config import Config
from configerus.loaded import Loaded, LOADED_KEY_ROOT
from configerus.validator import ValidationError
from configerus.contrib.jsonschema import PLUGIN_ID_VALIDATE_JSONSCHEMA

from .plugin import (
    METTA_PLUGIN_CONFIG_KEY_PLUGINID,
    METTA_PLUGIN_CONFIG_KEY_INSTANCEID,
    METTA_PLUGIN_CONFIG_KEY_ARGUMENTS,
    METTA_PLUGIN_CONFIG_KEY_PLUGINLABELS,
)
from .fixture import (
    Fixture,
    Fixtures,
    METTA_FIXTURE_CONFIG_KEY_PRIORITY,
    METTA_FIXTURES_CONFIG_FIXTURES_LABEL,
    METTA_FIXTURE_VALIDATION_JSONSCHEMA,
)

logger = getLogger("metta.env.mixins")

DEFAULT_FIXTURE_PRIORITY: int = 60
"""Default priority for plugin fixtures if not specified."""

METTA_PLUGIN_CONFIG_KEY_FROM_CONFIG = "from_config"
""" config key that indicates that the plugin will be build from aconfig label/key pair """


class FixtureBuildingFromConfigMixin:
    """Functions for building fixtures from config.

    This class contains various functions that can be used to build Fixtures
    by interpreting either Configerus Config data or raw Python primitives.
    The class can be used as a Mixin to add the standardized building approach
    to any object that can provide a Config source and a Fixture building
    callback.

    The provided Config object is used as an optional source of data for
    building, while the callback is passed raw Fixture building arguments as
    interpreted. This allows avoiding being too strict about how Fixtures are
    finally built and we can stay out of some ugly circular imports.

    """

    def __init__(
        self,
        config: Config,
        builder_callback: Callable[
            [str, str, int, Optional[Dict[str, Any]], Optional[Dict[str, Any]], Optional[bool]],
            Fixture,
        ],
        default_priority: int = DEFAULT_FIXTURE_PRIORITY,
    ):
        """Capture an environment used for constructor args for fixtures.

        Parameters:
        -----------
        config (Config) : A Configerus Config object which will be used as a
            source of information for building Fixtures by interpreting config
            as the parametrization for Fixture arguments.

        builder_callback (Callable) : A call back function which is meant to
            be used to actually build Fixtures from processed config.

            plugin_id (str) : METTA plugin id to tell us what plugin factory to use;

                @see .plugin.Factory for more details on how plugins are loaded.

            instance_id (str) : string instance id that will be passed to the new
                plugin object;

            priority (int) : Integer priority 1-100 for comparative prioritization
                between other plugins;

            arguments (Dict[str, Any]) : Keyword Arguments which should be passed to
                the plugin constructor after environment and instance_id;

            labels (Dict[str, str]) : Keyword/value labels which are to be associated
                with the plugin/fixture;

            replace_existing (bool) : Replace any existing matching fixture.

            e.g.

                def callback(
                        plugin_id: str,
                        instance_id: str,
                        priority: int,
                        arguments: Dict[str, Any] = None,
                        labels: Dict[str, Any] = None,
                        replace_existing=False,
                )


        """
        self._config: Config = config
        """Configerus Config object, for searching for fixture settings."""
        self.builder_callback: Callable = builder_callback
        """Callable callback ffixture factory used when settings are found."""
        self._default_priority: int = default_priority
        """Keep the default priority."""

    def plugin_priority(self, delta: int = 0):
        """Return a default plugin priority with a delta.

        Not sure what priority to give a plugin, or maybe you want a priority
        relative to a median; use this.

        Returns:
        --------
        Integer default priority with the provided delta added.

        """
        return self._default_priority + delta

    # Generic Plugin construction

    # pylint: disable=too-many-arguments
    # This is what it takes to build a plugin.
    def add_fixtures_from_config(
        self,
        label: str = METTA_FIXTURES_CONFIG_FIXTURES_LABEL,
        base: Union[str, List[Any]] = LOADED_KEY_ROOT,
        validator: str = "",
        exception_if_missing: bool = False,
        arguments: Dict[str, Any] = None,
        labels: Dict[str, str] = None,
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

        labels (Dict[str, str]) : Dictionary of labels which should be added to
            the created fixture.

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

        # plugin set which will be used to create new plugins
        fixtures: Fixtures = Fixtures()

        try:
            plugin_config = self._config.load(label)

            # check to see if we are being directed elsewhere for config
            # using a "from_config" directive
            try:
                config_fromconfig = plugin_config.get([base, METTA_PLUGIN_CONFIG_KEY_FROM_CONFIG])

                if isinstance(config_fromconfig, dict):
                    logger.debug("Using from_config, and passing label/base as arguments")
                    label = plugin_config.get(
                        [base, METTA_PLUGIN_CONFIG_KEY_FROM_CONFIG, "label"], default=label
                    )
                    base = plugin_config.get(
                        [base, METTA_PLUGIN_CONFIG_KEY_FROM_CONFIG, "base"],
                        default=LOADED_KEY_ROOT,
                    )

                    plugin_config = self._config.load(label)
                else:
                    logger.debug("Using from_config, and passing current label/base as arguments")
            except KeyError:
                pass
            plugin_list = plugin_config.get(base)

        except KeyError as err:
            if exception_if_missing:
                raise KeyError("Could not load any config for plugin generation") from err
            return fixtures

        for instance_id in plugin_list.keys():
            # We only accept string instance ids
            instance_id = str(instance_id)

            # This fixture gets effectively added to 2 different Fixtures object.
            # 1. we manually add it to our Fixtures object for this function call
            # 2. the add_fixture_from_config() adds it to the fixture for this
            #    environment object.
            fixture = self.add_fixture_from_config(
                label=label,
                base=[base, instance_id] if base else instance_id,
                instance_id=instance_id,
                labels=labels,
                validator=validator,
                arguments=arguments,
            )
            fixtures.add(fixture)

        return fixtures

    # pylint: disable=too-many-arguments
    # This is what it takes to build a plugin.
    def add_fixture_from_config(
        self,
        label: str,
        base: Union[str, List[Any]] = LOADED_KEY_ROOT,
        instance_id: str = "",
        priority: int = -1,
        validator: str = "",
        arguments: Dict[str, Any] = None,
        labels: Dict[str, str] = None,
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

        labels (Dict[str, str]) : Dictionary of labels which should be added to
            the created fixture.

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
            # loaded configuration for the plugin
            plugin_loaded = self._config.load(label)
        except KeyError as err:
            raise KeyError(f"Could not load plugin config source {label}") from err

        # if no arguments were specified, then consider a special case of
        # 'from_config' which build arguments for a config based plugin
        # which will take a config label/base-key pair as config arguments
        #
        # There is a special case where if the passed from_config is not a
        # dict then the same config label/base received is used.
        try:
            config_fromconfig = plugin_loaded.get([base, METTA_PLUGIN_CONFIG_KEY_FROM_CONFIG])

            if isinstance(config_fromconfig, dict):
                logger.debug("Using from_config, and passing label/base as arguments")
                arguments = config_fromconfig
            else:
                logger.debug("Using from_config, and passing current label/base as arguments")
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
            labels=labels,
        )

    # This is where we centralize all logic around creating fixtures, so it is complex
    # pylint: disable=too-many-branches, too-many-locals, too-many-arguments
    def add_fixture_from_loadedconfig(
        self,
        loaded: Loaded,
        base: Union[str, List[Any]] = LOADED_KEY_ROOT,
        instance_id: str = "",
        priority: int = -1,
        labels: Dict[str, str] = None,
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

        labels (Dict[str, str]) : Dictionary of labels which should be added to
            the created fixture.

        arguments (Dict[str, str]) : Dictionary of args which should be passed
            to the plugin constructor.

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
        if not loaded.has(base):
            raise ValueError("Cannot build plugin as provided config was empty.")

        # get any validators from config, defaulting to just the jsonschema
        # validator for a fixture
        validators = loaded.get(
            [base, METTA_FIXTURE_VALIDATION_JSONSCHEMA],
            default=[{PLUGIN_ID_VALIDATE_JSONSCHEMA: METTA_FIXTURE_VALIDATION_JSONSCHEMA}],
        )

        if validator:
            # if a validator arg was passed in, then add it
            validators.append(validator)
        if len(validators):
            # Run configerus validation on the config base once per validator
            try:
                for val in validators:
                    loaded.get(base, validator=val)
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
            instance_id = str(loaded.get([base, METTA_PLUGIN_CONFIG_KEY_INSTANCEID], default=""))
            if not instance_id:
                instance_rand = "".join(random.choice(string.ascii_lowercase) for i in range(10))
                instance_id = f"{plugin_id}-{instance_rand}"

        if priority < 0:
            # instance priority - this is actually a stupid way to get it
            priority = int(
                loaded.get(
                    [base, METTA_FIXTURE_CONFIG_KEY_PRIORITY],
                    default=self.plugin_priority(),
                )
            )

        config_arguments = loaded.get([base, METTA_PLUGIN_CONFIG_KEY_ARGUMENTS], default={})
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

        config_labels = loaded.get([base, METTA_PLUGIN_CONFIG_KEY_PLUGINLABELS], default={})
        if len(config_labels) > 0:
            if labels is None:
                labels = {}
            else:
                labels = labels.copy()

            labels.update(config_labels)

        # Use the factory to make the .fixture.Fixture
        return self.builder_callback(
            plugin_id=plugin_id,
            instance_id=instance_id,
            priority=priority,
            arguments=arguments,
            labels=labels,
        )


class FixtureBuildingFromDictMixin:
    """Functions for building fixtures from Dicts.

    This class contains various functions that can be used to build Fixtures
    by interpreting either Configerus Config data or raw Python primitives.
    The class can be used as a Mixin to add the standardized building approach
    to any object that can provide Dict sources and a Fixture building
    callback.

    The callback is passed raw Fixture building arguments as
    interpreted. This allows avoiding being too strict about how Fixtures are
    finally built and we can stay out of some ugly circular imports.

    """

    def __init__(
        self,
        builder_callback: Callable[[str, str, int, Dict[str, Any], Dict[str, Any], bool], Fixture],
    ):
        """Capture an environment used for constructor args for fixtures.

        Parameters:
        -----------
        builder_callback (Callable) : A call back function which is meant to
            be used to actually build Fixtures from processed config.

            plugin_id (str) : METTA plugin id to tell us what plugin factory to use;

                @see .plugin.Factory for more details on how plugins are loaded.

            instance_id (str) : string instance id that will be passed to the new
                plugin object;

            priority (int) : Integer priority 1-100 for comparative prioritization
                between other plugins;

            arguments (Dict[str, Any]) : Keyword Arguments which should be passed to
                the plugin constructor after environment and instance_id;

            labels (Dict[str, str]) : Keyword/value labels which are to be associated
                with the plugin/fixture;

            replace_existing (bool) : Replace any existing matching fixture.

            e.g.

                def callback(
                        plugin_id: str,
                        instance_id: str,
                        priority: int,
                        arguments: Dict[str, Any] = None,
                        labels: Dict[str, Any] = None,
                        replace_existing=False,
                )


        """
        self.builder_callback: Callable = builder_callback
        """Callable callback ffixture factory used when settings are found."""

    # Generic Plugin construction

    def add_fixtures_from_dicts(
        self,
        plugins_list: List[Dict[str, Any]],
    ) -> Fixtures:
        """Create a Fixtures set if Fixtures from dict parameters."""
        fixtures: Fixtures = Fixtures()

        for plugin_dict in plugins_list:
            fixture = self.add_fixture_from_dict(plugin_dict)
            fixtures.add(fixture)

        return fixtures

    def add_fixture_from_dict(
        self,
        plugin_dict: Dict[str, Any],
    ) -> Fixture:
        """Create a single plugin from a Dict of information for it.

        Create a new plugin from a map/dict of settings for needed parameters.

        @see add_fixture_from_loadedconfig

        Parameters:
        -----------
        client_dict (Dict[str,Any]) : Dict from which all needed information will
            be pulled.  Optionally additional config sources can be included as
            well as arguments which could be passed to the plugin.

        Return:
        -------
        A Fixture object with the new plugin added

        The Fixtures has already been added to the environment, but is returned
        so that the consumer can act on it separately without haveing to
        search for it.

        """
        try:
            plugin_id = str(plugin_dict[METTA_PLUGIN_CONFIG_KEY_PLUGINID])
        except KeyError as err:
            raise ValueError(
                "Could not find a plugin_id when trying to create a "
                f"plugin from dict: {plugin_dict}"
            ) from err

        # if no instance_id was passed, try to load one or just make one up
        if METTA_PLUGIN_CONFIG_KEY_INSTANCEID in plugin_dict:
            instance_id = str(plugin_dict[METTA_PLUGIN_CONFIG_KEY_INSTANCEID])
        else:
            instance_rand = "".join(random.choice(string.ascii_lowercase) for i in range(10))
            instance_id = f"{plugin_id}-{instance_rand}"

        # instance priority - this is actually a stupid way to get it
        priority = 70
        if METTA_FIXTURE_CONFIG_KEY_PRIORITY in plugin_dict:
            priority = int(plugin_dict[METTA_FIXTURE_CONFIG_KEY_PRIORITY])

        arguments: Dict[str, Any] = {}
        if METTA_PLUGIN_CONFIG_KEY_ARGUMENTS in plugin_dict:
            arguments.update(plugin_dict[METTA_PLUGIN_CONFIG_KEY_ARGUMENTS])

        labels: Dict[str, Any] = {}
        if METTA_PLUGIN_CONFIG_KEY_PLUGINLABELS in plugin_dict:
            labels.update(plugin_dict[METTA_PLUGIN_CONFIG_KEY_PLUGINLABELS])

        # Use the factory to make the .fixture.Fixture
        fixture = self.builder_callback(
            plugin_id=plugin_id,
            instance_id=instance_id,
            priority=priority,
            arguments=arguments,
            labels=labels,
        )

        return fixture
