"""

A state that uses labels to manage fixtures on activation.

"""
from typing import List
from logging import getLogger

from mirantis.testing.metta.provisioner import METTA_PLUGIN_INTERFACE_ROLE_PROVISIONER
from mirantis.testing.metta.workload import METTA_PLUGIN_INTERFACE_ROLE_WORKLOAD
from mirantis.testing.metta_health.healthcheck import METTA_PLUGIN_INTERFACE_ROLE_HEALTHCHECK

from .state import EnvironmentStatePlugin


logger = getLogger("metta_state:activatingstate")

METTA_STATE_LABELACTIVATE_PLUGIN_ID = "metta_state_labelactivate"
""" Metta plugin id for the label activate environment state plugin."""

METTA_STATE_LABEL_ACTIVATE = "state-activate"
"""Metta fixture label that indicates that this fixture should activate on a state."""


class EnvironmentLabelActivateStatePlugin(EnvironmentStatePlugin):
    """A State piece of a StateBasedEnvironment that processes fixture labels on activate."""

    # Use State bootstrappers as well as env bootastrappers
    def activate(self):
        """Respond to the state being activated."""
        errors: List[Exception] = []
        for fixture in self.fixtures().filter(
            labels={METTA_STATE_LABEL_ACTIVATE: self.instance_id()}
        ):

            # Provisioner and Workload plugins are activated by running "apply"
            if (
                METTA_PLUGIN_INTERFACE_ROLE_PROVISIONER in fixture.interfaces
                or METTA_PLUGIN_INTERFACE_ROLE_WORKLOAD in fixture.interfaces
            ):
                try:
                    logger.info("Activating fixture %s:%s", fixture.plugin_id, fixture.instance_id)
                    fixture.plugin.prepare()
                    fixture.plugin.apply()
                # pylint: disable=broad-except
                except Exception as err:
                    logger.warning(
                        "Failed activating fixture %s:%s : %s",
                        fixture.plugin_id,
                        fixture.instance_id,
                        err,
                    )
                    errors.append(
                        RuntimeError(
                            f"Failed activating fixture {fixture.plugin_id}:{fixture.instance_id}"
                            f" : {err}"
                        )
                    )

            elif METTA_PLUGIN_INTERFACE_ROLE_HEALTHCHECK in fixture.interfaces:
                try:
                    logger.info(
                        "Checking fixture health %s:%s", fixture.plugin_id, fixture.instance_id
                    )
                    fixture.plugin.health()
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
