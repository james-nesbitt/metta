"""

An environment that operates from a set of states.

The idea here is to provide functionality for progression of an environment
across a set of states.  For this, a state is an environment definition itself;
a container of config and fixtures, themselves contained in a environment.

The code here is not very elegant, but what we do is we provide an environment
plugin which will create a number of state plugins which can be activated. If
an environment is asked for config of fixtures, it retrieves them fromt the
currently active state.  You can ask the environment to switch to a different
state.

Some foolishness is in place for the initial construction, and the current
implementation doesn't share anythin across states except initial config copy()
but the concept works.

As Environments are effectively declarative, this initial functionality does not
restrict state changes (like forcing a forward only progression) but that could
be added if we decide that this code is worth keeping.


I think that these state plugins are not safe to generate across threads at the
same time. This comes down to the need to copy/duplicate the config option.

"""
from typing import Dict, Any
from logging import getLogger

from configerus.config import Config
from configerus.loaded import LOADED_KEY_ROOT

from mirantis.testing.metta.fixture import (
    Fixtures,
    METTA_FIXTURES_CONFIG_FIXTURES_LABEL,
)
from mirantis.testing.metta.environment import (
    Environment,
    FixtureBuilderEnvironment,
    METTA_ENTRYPOINT_BOOTSTRAP_ENVIRONMENT,
)
from mirantis.testing.metta.building import (
    FixtureBuildingFromConfigMixin,
    FixtureBuildingFromDictMixin,
)
from mirantis.testing.metta.config import (
    add_config_sources_from_config,
    METTA_CONFIG_CONFIG_SOURCE_KEY,
)
from mirantis.testing.metta.importing import add_imports_from_config, METTA_IMPORT_CONFIG_LABEL
from mirantis.testing.metta.setuptools import (
    setuptools_entrypoint,
    METTA_CONFIG_SETUPTOOLS_BOOTSTRAPS_KEY,
)

logger = getLogger("metta_state.defaultstate")

METTA_PLUGIN_INTERFACE_ROLE_ENVIRONMENTSTATE = "state"
"""Plugin interface to behave as an environment state in a StateBasedEnvironment."""

METTA_ENTRYPOINT_BOOTSTRAP_STATE = "metta.bootstraps.states"
"""Setup tools entrypoints for bootstrapping a state object."""

METTA_FIXTURES_CONFIG_STATES_KEY = "states"
"""Configerus .get() base key for retrieving states from config."""


METTA_STATE_DEFAULT_PLUGIN_ID = "metta_state_default"
""" Metta plugin id for the standard environment state plugin."""


# we use the parent methods, but override the constructor.
# pylint: disable=super-init-not-called
class EnvironmentStatePlugin(FixtureBuilderEnvironment):
    """A State piece of a StateBasedEnvironment."""

    def __init__(
        self,
        environment: Environment,
        instance_id: str,
        label: str = METTA_FIXTURES_CONFIG_STATES_KEY,
        base: Any = LOADED_KEY_ROOT,
    ):
        """Run the super constructor but also set class properties.

        Interpret provided config and configure the object with all of the
        needed pieces for executing terraform commands.

        This repeats a lof of the Environment functionality as an override,
        mainly so that we can change some small details about plugin generation.

        """
        self._environment: Environment = environment
        """ Environemnt in which this plugin exists """
        self._instance_id: str = instance_id
        """ Unique id for this plugin instance """

        self._config: Config = environment._config
        """Config object, overridden in activate()."""

        self._config_label = label
        """ configerus load label that should contain all of the config """
        self._config_base = base
        """ configerus get key that should contain all tf config """

        self._fixtures: Fixtures = Fixtures()
        """Children fixtures, typically just the client plugin."""

    # Use State bootstrappers as well as env bootastrappers
    def activate(self):
        """Respond to the state being activated."""
        logger.debug("Default state plugin activated: %s", self.instance_id())

        # Use the protected config so that we don't use a state config by accident
        # pylint: disable=protected-access`
        self._config = self._config.copy()
        Environment.__init__(self, config=self._config, instance_id=self._instance_id)
        FixtureBuildingFromConfigMixin.__init__(
            self, config=self._config, builder_callback=self.new_fixture
        )
        FixtureBuildingFromDictMixin.__init__(self, builder_callback=self.new_fixture)

        # If we received any config directiosn, then we self-bootstrap from the config
        if self._config_label:
            # 1. add any config sources specified in config
            # (Here config tells us to load more config. It is weird but ok.)
            add_config_sources_from_config(
                config=self._config,
                label=self._config_label,
                base=[self._config_base, METTA_CONFIG_CONFIG_SOURCE_KEY],
            )

            # 2. import any python code requested, to make sure that all funxtionality
            #    is in scope that is needed.
            #    Here we say look in the "metta" config for a "imports" section.
            add_imports_from_config(
                config=self._config,
                label=self._config_label,
                base=[self._config_base, METTA_IMPORT_CONFIG_LABEL],
            )

            # 3. run an setuptools bootstrap entrypoints
            env_config = self._config.load(self._config_label)
            environment_boostraps = env_config.get(
                [self._config_base, METTA_CONFIG_SETUPTOOLS_BOOTSTRAPS_KEY], default=[]
            )
            setuptools_entrypoint(
                entrypoint=METTA_ENTRYPOINT_BOOTSTRAP_ENVIRONMENT,
                entries=environment_boostraps,
                args=[self],
                kwargs={},
            )

            # 4. build fixtures from config
            labels: Dict[str, str] = {
                "container": "state",
                "container_id": self.instance_id(),
                "state": self.instance_id(),
                "environment": self._environment.instance_id(),
            }
            self.add_fixtures_from_config(
                label=self._config_label,
                base=[self._config_base, METTA_FIXTURES_CONFIG_FIXTURES_LABEL],
                labels=labels,
            )

    # pylint: disable=unused-argument
    def info(self, deep: bool = False) -> Dict[str, Any]:
        """Return dict plugin info."""
        state_info = {
            "name": self.instance_id(),
            # "boostraps": self._environment_boostraps,
        }

        if deep:
            state_info["fixtures"] = self._fixtures.info(deep=deep)

        return state_info
