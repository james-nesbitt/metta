"""

A state that uses labels to manage fixtures on activation.

"""
from typing import List, Dict, Any, Union
from logging import getLogger

from configerus.loaded import Loaded

from mirantis.testing.metta.fixture import Fixture
from mirantis.testing.metta.provisioner import METTA_PLUGIN_INTERFACE_ROLE_PROVISIONER
from mirantis.testing.metta.workload import METTA_PLUGIN_INTERFACE_ROLE_WORKLOAD
from mirantis.testing.metta_health.healthcheck import METTA_PLUGIN_INTERFACE_ROLE_HEALTHCHECK

from .state import EnvironmentStatePlugin


logger = getLogger("metta_state:activatingstate")

METTA_STATE_LABELACTIVATE_PLUGIN_ID = "metta_state_labelactivate"
""" Metta plugin id for the label activate environment state plugin."""

METTA_STATE_FIXTURE_LABEL_ACTIVATE = "state-activate"
"""Metta fixture label that indicates that this fixture should activate on a state."""

METTA_STATE_FIXTURE_LABEL_DEACTIVATE = "state-deactivate"
"""Metta fixture label that indicates that this fixture should deactivate on a state."""


class EnvironmentLabelActivateStatePlugin(EnvironmentStatePlugin):
    """A State piece of a StateBasedEnvironment that processes fixture labels on activate."""

    def info(self, deep: bool = False) -> Dict[str, Any]:
        """Return Dict of introspective information about the plugin."""
        state_config: Loaded = self.config().load(self._config_label)

        plugin_info: Dict[str, Any] = super().info(deep=deep)
        plugin_info["activate"] = state_config.get(
            [self._config_base, METTA_STATE_FIXTURE_LABEL_ACTIVATE], default="NONE"
        )

        return plugin_info

    def activate(self):
        """Activate the state plugin.

        This means using config data for the state plugin, and labels for the
        contained fixtures for taking actions on them.
        """
        # parent activate to load fixtures/config
        super().activate()

        # Method 1: activate any fixtures with labels directing activation on
        #    this state.
        self._activate_fixtures_with_labels()

        # method 2: activate any fixtures based on configuration from the state.
        self._activate_fixture_using_state_config()

    def _activate_fixture_using_state_config(self):
        """Use state config to decide to activate fixtures."""
        errors: List[Exception] = []

        state_config: Loaded = self.config().load(self._config_label)

        fixtures_to_activate: List[Union[str, Dict[str, str]]] = state_config.get(
            [self._config_base, METTA_STATE_FIXTURE_LABEL_ACTIVATE], default=[]
        )
        try:
            iter(fixtures_to_activate)
        except TypeError as err:
            raise RuntimeError(
                f"Fixtures to activate was not an iterator of instance_ids: {fixtures_to_activate}"
            ) from err

        for fixture_def in fixtures_to_activate:
            if isinstance(fixture_def, str):
                fixture_def = {"instance_id": fixture_def}
            fixture = self.fixtures().get(**fixture_def)

            try:
                _activate_fixture(fixture)

            # pylint: disable=broad-except
            except Exception as err:
                logger.warning(
                    "Failed checking health %s:%s : %s",
                    fixture.plugin_id,
                    fixture.instance_id,
                    err,
                )
                errors.append(
                    RuntimeError(
                        f"Failed checking fixture health {fixture.plugin_id}:{fixture.instance_id}"
                        f" : {err}"
                    )
                )

        if len(errors) > 0:
            raise RuntimeError(
                "Environment state encountered errors while activating on state labels.", errors
            )

    def _activate_fixtures_with_labels(self):
        """Activate contained fixtures if they have the right labels."""
        errors: List[Exception] = []
        for fixture in self.fixtures().filter(
            labels={METTA_STATE_FIXTURE_LABEL_ACTIVATE: self.instance_id()},
            exception_if_missing=False,
        ):
            try:
                _activate_fixture(fixture)

            # pylint: disable=broad-except
            except Exception as err:
                logger.warning(
                    "Failed checking health %s:%s : %s",
                    fixture.plugin_id,
                    fixture.instance_id,
                    err,
                )
                errors.append(
                    RuntimeError(
                        f"Failed checking fixture health {fixture.plugin_id}:{fixture.instance_id}"
                        f" : {err}"
                    )
                )

        if len(errors) > 0:
            raise RuntimeError(
                "Environment state encountered errors while activating on labels.", errors
            )


def _activate_fixture(fixture: Fixture):
    """Activate a passed fixture, depending on interfaces.

    Returns:
    --------
    Exception that was thrown or None
    """
    # Provisioner and Workload plugins are activated by running "apply"
    if (
        METTA_PLUGIN_INTERFACE_ROLE_PROVISIONER in fixture.interfaces
        or METTA_PLUGIN_INTERFACE_ROLE_WORKLOAD in fixture.interfaces
    ):
        logger.warning("Activating fixture %s:%s", fixture.plugin_id, fixture.instance_id)
        fixture.plugin.prepare()
        fixture.plugin.apply()

    elif METTA_PLUGIN_INTERFACE_ROLE_HEALTHCHECK in fixture.interfaces:
        logger.warning("Checking fixture health %s:%s", fixture.plugin_id, fixture.instance_id)
        fixture.plugin.health()

    else:
        raise ValueError(
            f"Fixture '{fixture.instance_id} was not activated because it "
            "had no activatable interface."
        )
