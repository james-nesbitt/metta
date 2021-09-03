"""

Environment definitions and functionality.

An environment in Metta is a container for the metta components. It is created
early and used to access all of the metta functionality.  For testing systems,
you can think of an environment as a collection of interconnected resources to
be managed together. If components need to be started or stopped together then
they are probably a part of the same environment.
When using Metta you can use more than one Environment object, but often you
don't need to.

The two primary components of an environment are:
1. A configerus config object to be shared by functionality that identifies as
  being in the environment.  This includes Metta components, but is intended to
  be used by external components as well.
2. A Fixtures set of Metta Fixture/Plugin components created in the environment.

In this file are defined two Environment plugins:

1. Default : a bare bones environment object, which you can use in any project
             to manually create fixtures/plugins and access them.
2. Builder : an environment with a number builder functions added to make it
             easier to create plugins en masse, using configerus config or from
             dicts of data.
             This environment also uses config for importing more python modules
             and for adding configerus config sources at runtime.

Almost all of the Mirantis test suites use the builder or a derivative, and the
default environment is there primarily as a stripped down simple version.

"""
from typing import Dict, List, Any
from logging import getLogger

from configerus.config import Config
from configerus.loaded import LOADED_KEY_ROOT

from .plugin import (
    Factory,
)
from .fixture import (
    Fixture,
    Fixtures,
    METTA_FIXTURES_CONFIG_FIXTURES_LABEL,
)
from .building import FixtureBuildingFromConfigMixin, FixtureBuildingFromDictMixin
from .config import add_config_sources_from_config, METTA_CONFIG_CONFIG_SOURCE_KEY
from .importing import add_imports_from_config, METTA_IMPORT_CONFIG_LABEL
from .setuptools import setuptools_entrypoint, METTA_CONFIG_SETUPTOOLS_BOOTSTRAPS_KEY

logger = getLogger("metta.environment")

METTA_ENTRYPOINT_BOOTSTRAP_ENVIRONMENT = "metta.bootstrap.environment"
"""Setuptools entrypoint for boostrapping environments."""

METTA_PLUGIN_INTERFACE_ROLE_ENVIRONMENT = "environment"
""" metta plugin interface identifier for environment plugins """


METTA_FIXTURES_CONFIG_ENVIRONMENTS_KEY = "environments"
"""Configerus .get() key for finding environments."""


METTA_CORE_ENVIRONMENT_PLUGIN_ID = "metta_core_environment"
""" Metta plugin id for the base environment plugin.

In the Factory below, this ID is used to register the factory function which
builds an instance of the "Environment" class, defined a few lines below.

That Environment plugin is meant to be used as a simple Environment
implementation with enough functionality to be fully usable. See also the
Builder plugin which has more code to generate plugins automatically.

"""


@Factory(
    plugin_id=METTA_CORE_ENVIRONMENT_PLUGIN_ID,
    interfaces=[METTA_PLUGIN_INTERFACE_ROLE_ENVIRONMENT],
)
def core_environment_factory(config: Config, instance_id: str) -> "Environment":
    """Build a FixtureBuilderEnvironment environment."""
    return Environment(config=config, instance_id=instance_id)


class Environment:
    """Environment with helpers for building fixtures.

    The building Environment handler is a straight forward bare Environment
    object with additional helper methods to build fixtures in the Environment.

    This separates out the two base needs for an environment:
    1. the simple raw interactive functionality for the Environment,
    2. the magic config and Dict interpration for building Fixtures

    The combination makes this class quite bare, but allows other Environment
    objects to add on more functionality without creating import circuits.
    """

    def __init__(self, config: Config, instance_id: str):
        """Get an environment name and a config object.

        Parameters:
        -----------
        instance_id (str) : Arbitrary string label for the environment, not used for
            any functionality, and so not limited in uniqueness or syntax.
        config (Config) : Configerus Config object used internally and by any
            functionality that wants to consider itself inside the environment.

        """
        self._instance_id: str = instance_id
        """Arbitrary label for the environment, not used functionally."""
        self._config: Config = config
        """Config object usable by any component that is in the env."""
        self._fixtures: Fixtures = Fixtures()
        """An environment is a container of Fixture objects."""

    # pylint: disable=unused-argument
    def info(self, deep: bool = False) -> Dict[str, Any]:
        """Return dict plugin info."""
        return {
            "name": self.instance_id(),
        }

    def set_state(self, state: str):
        """Indicate to an Environment what state is expected.

        This is an injection option which needs to be at this base object, but
        is meant to allow different Environment plugin classes to respond in
        any manner.
        The method has a very simple interface, because it needs to be generic.

        This was develloped with the contrib state based environments in mind,
        and is actually a leftover from the previous state design, but I don't
        have an abstract way to pull it out without big overhauls and even more
        abstractions and overrides.  Right now this facilitates the cli control
        for state.

        """
        logger.warning(
            "Environment %s doesn't accomodate state changes: %s", self._instance_id, state
        )

    def instance_id(self) -> str:
        """Get the string label for the environment.

        Returns:
        --------
        String label for the environment
        """
        return self._instance_id

    def config(self) -> Config:
        """Configerus Config access for the environment.

        Returns:
        --------
        A Configerus Config object which is meant to be used by anything inside
        the environment.
        """
        return self._config

    def fixtures(self) -> Fixtures:
        """Fixtures collection accessor for the environment.

        Returns:
        --------
        A Fixtures object which is a set of all Fixture/Plugin compoents in the
        environment.
        """
        return self._fixtures

    # This is what it takes to build a plugin
    # pylint: disable=too-many-arguments
    def new_fixture(
        self,
        plugin_id: str,
        instance_id: str,
        priority: int,
        arguments: Dict[str, Any] = None,
        labels: Dict[str, Any] = None,
        replace_existing=False,
    ) -> Fixture:
        """Create a new plugin from parameters.

        Parameters:
        -----------
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

        # Catch some early arg validation errors which would otherwise have
        # caused some hard to diagnose issues.
        if not (
            isinstance(plugin_id, str)
            and isinstance(instance_id, str)
            and isinstance(priority, int)
        ):
            raise ValueError(
                f"Bad arguments passed for creating a fixture: "
                f":{plugin_id}:{instance_id} ({priority})"
            )

        if labels is None:
            labels = {}
        labels["environment"] = self.instance_id()

        # Build the plugin instance by passing collected arguments to the
        # registered plugin factory. This will call whatever function was
        # decorated for the plugin_id.
        args: List[Any] = [self, instance_id]
        kwargs: Dict[str, Any] = arguments
        plugin_instance = Factory.create(plugin_id, instance_id, *args, **kwargs)

        # Build a fixture from the plugin_instance and add it to the fixtures
        # set for the environment, then return the fixture.
        fixture = self.fixtures().add(
            fixture=Fixture.from_instance(plugin_instance, priority=priority, labels=labels),
            replace_existing=replace_existing,
        )
        return fixture


METTA_BUILDER_ENVIRONMENT_PLUGIN_ID = "metta_builder_environment"
""" Metta plugin id for the classic environment plugin.

In the Factory below, this ID is used to register the factory function which
builds an instance of the "FixtureBuilderEnvironment" class, defined a few
lines below.

The Builder environment includes code for more automated inclusion, configuration
and creation of environment plugins, either from config or from dicts.
If you like config based environments, this is likely what you want.
"""


@Factory(
    plugin_id=METTA_BUILDER_ENVIRONMENT_PLUGIN_ID,
    interfaces=[METTA_PLUGIN_INTERFACE_ROLE_ENVIRONMENT],
)
def builder_environment_factory(
    config: Config, instance_id: str, label: str = "", base: str = LOADED_KEY_ROOT
) -> "FixtureBuilderEnvironment":
    """Build a FixtureBuilderEnvironment environment."""
    return FixtureBuilderEnvironment(
        config=config, instance_id=instance_id, label=label, base=base
    )


class FixtureBuilderEnvironment(
    Environment, FixtureBuildingFromConfigMixin, FixtureBuildingFromDictMixin
):
    """Environment with helpers for building fixtures.

    The building Environment handler is a straight forward bare Environment
    object with additional helper methods to build fixtures in the Environment.

    This separates out the the magic config and Dict interpration for building
    Fixtures from the base Environment object.  Both can be used, but this one
    attempts to make plugin generation easier.

    The combination makes this class quite bare, but allows other Environment
    objects to add on more functionality without creating import circuits.
    """

    def __init__(
        self, config: Config, instance_id: str, label: str = "", base: str = LOADED_KEY_ROOT
    ):
        """Get an environment name and a config object.

        Parameters:
        -----------
        name (str) : Arbitrary string label for the environment, not used for
            any functionality, and so not limited in uniqueness or syntax.
        config (Config) : Configerus Config object used internally and by any
            functionality that wants to consider itself inside the environment.
        """
        Environment.__init__(self, config=config, instance_id=instance_id)
        FixtureBuildingFromConfigMixin.__init__(
            self, config=config, builder_callback=self.new_fixture
        )
        FixtureBuildingFromDictMixin.__init__(self, builder_callback=self.new_fixture)

        self._environment_boostraps: List[str] = []
        """Track what bootstaps we have applied for introspection."""

        # If we received any config directiosn, then we self-bootstrap from the config
        if label:
            env_config = config.load(label)

            # 1. add any config sources specified in config
            # (Here config tells us to load more config. It is weird but ok.)
            add_config_sources_from_config(
                config=config, label=label, base=[base, METTA_CONFIG_CONFIG_SOURCE_KEY]
            )

            # 2. import any python code requested, to make sure that all funxtionality
            #    is in scope that is needed.
            #    Here we say look in the "metta" config for a "imports" section.
            add_imports_from_config(
                config=config, label=label, base=[base, METTA_IMPORT_CONFIG_LABEL]
            )

            # 3. run an setuptools bootstrap entrypoints
            self._environment_boostraps = env_config.get(
                [base, METTA_CONFIG_SETUPTOOLS_BOOTSTRAPS_KEY], default=[]
            )
            setuptools_entrypoint(
                entrypoint=METTA_ENTRYPOINT_BOOTSTRAP_ENVIRONMENT,
                entries=self._environment_boostraps,
                args=[self],
                kwargs={},
            )

            # 4. build fixtures from config
            try:
                labels: Dict[str, str] = {
                    "container": "environment",
                    "container_id": self.instance_id(),
                    "environment": self.instance_id(),
                }
                self.add_fixtures_from_config(
                    label=label,
                    base=[base, METTA_FIXTURES_CONFIG_FIXTURES_LABEL],
                    labels=labels,
                )
            except KeyError as err:
                logger.warning(
                    "%s Environment plugin encountered an issue creating fixtures: %s",
                    self.__class__,
                    err,
                )

    # pylint: disable=unused-argument
    def info(self, deep: bool = False) -> Dict[str, Any]:
        """Return dict plugin info."""
        return {
            "name": self.instance_id(),
            "bootstraps": self._environment_boostraps,
        }
