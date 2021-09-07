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

"""
from typing import Dict, Any

from configerus.config import Config
from configerus.loaded import LOADED_KEY_ROOT

from mirantis.testing.metta.fixture import (
    Fixture,
    Fixtures,
)
from mirantis.testing.metta.environment import (
    FixtureBuilderEnvironment,
)


METTA_PLUGIN_INTERFACE_ROLE_ENVIRONMENTSTATE = "state"
"""Plugin interface to behave as an environment state in a StateBasedEnvironment."""

METTA_ENTRYPOINT_BOOTSTRAP_STATE = "metta.bootstraps.states"
"""Setup tools entrypoints for bootstrapping a state object."""

METTA_FIXTURES_CONFIG_STATES_KEY = "states"
"""Configerus .get() base key for retrieving states from config."""


METTA_ENVIRONMENT_STATE_PLUGIN_ID = "metta_state_environment"
""" Metta plugin id for the state based environment plugin."""


class StateBasedEnvironment(FixtureBuilderEnvironment):
    """An environment implementation that keeps states."""

    def __init__(
        self, config: Config, instance_id: str, label: str = "", base: str = LOADED_KEY_ROOT
    ):
        """Create the StateBased environment components."""
        self._active_state_id: str = ""
        """Currently active state fixture/plugin."""
        FixtureBuilderEnvironment.__init__(
            self, config=config, instance_id=instance_id, label=label, base=base
        )

        # Build all of the state plugins
        labels: Dict[str, str] = {
            "container": "environment",
            "container_id": self.instance_id(),
            "environment": self.instance_id(),
        }

        try:
            self.add_fixtures_from_config(
                label=label,
                base=[base, METTA_FIXTURES_CONFIG_STATES_KEY],
                labels=labels,
                exception_if_missing=True,
            )

        except KeyError as err:
            raise RuntimeError(f"State environment could't create states: {err}") from err

        # Activate the highest priority state plugin
        self.set_state(
            self._fixtures.get(
                interfaces=[METTA_PLUGIN_INTERFACE_ROLE_ENVIRONMENTSTATE]
            ).instance_id
        )

    # pylint: disable=unused-argument
    def info(self, deep: bool = False) -> Dict[str, Any]:
        """Return dict plugin info."""
        return {
            "name": self.instance_id(),
            "boostraps": self._environment_boostraps,
            "active_state": self._active_state_id,
            "states": self._fixtures.filter(
                interfaces=[METTA_PLUGIN_INTERFACE_ROLE_ENVIRONMENTSTATE]
            ).info(deep=deep),
        }

    def set_state(self, state: str):
        """Change to a different active state."""
        try:
            state_fixture: Fixture = self._fixtures.get(
                instance_id=state, interfaces=[METTA_PLUGIN_INTERFACE_ROLE_ENVIRONMENTSTATE]
            )

        except KeyError as err:
            raise RuntimeError(f"Unknown State requested for activation: {state}") from err

        self._active_state_id = state_fixture.instance_id

        # activate the state plugin
        if hasattr(state_fixture.plugin, "activate"):
            state_fixture.plugin.activate()

    def _get_active_state_fixture(self) -> Fixture:
        """Get the active state fixture."""
        return self._fixtures.get(
            instance_id=self._active_state_id,
            interfaces=[METTA_PLUGIN_INTERFACE_ROLE_ENVIRONMENTSTATE],
        )

    def config(self) -> Config:
        """Return the Config from the active state."""
        if self._active_state_id:
            return self._get_active_state_fixture().plugin.config()
        return self._config

    def fixtures(self) -> Fixtures:
        """Return the Fixtures from the active state."""
        if self._active_state_id:
            return self._get_active_state_fixture().plugin.fixtures()
        return self._fixtures
