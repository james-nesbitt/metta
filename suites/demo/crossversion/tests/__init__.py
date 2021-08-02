"""

Cross version testing package

"""
import logging
import json
from typing import Any, Dict

import pytest

from configerus.loaded import LOADED_KEY_ROOT

from mirantis.testing.metta import get_environment
from mirantis.testing.metta.fixtures import Fixtures
from mirantis.testing.metta.provisioner import METTA_PLUGIN_INTERFACE_ROLE_PROVISIONER
from mirantis.testing.metta.client import METTA_PLUGIN_INTERFACE_ROLE_CLIENT
from mirantis.testing.metta.healthcheck import METTA_PLUGIN_INTERFACE_ROLE_HEALTHCHECK, Health, HealthStatus

from mirantis.testing.metta_common import METTA_PLUGIN_ID_PROVISIONER_COMBO
from mirantis.testing.metta_launchpad import METTA_LAUNCHPAD_PROVISIONER_PLUGIN_ID
from mirantis.testing.metta_mirantis.mke_client import (
    MKENodeState,
    METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID,
)
from mirantis.testing.metta_mirantis.msr_client import (
    MSRReplicaHealth,
    METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID,
)


logger = logging.getLogger("base")


class EnvManager:
    """Base testing class that knows how to detect stability in a cluster."""

    __test__ = False

    def __init__(self, env_name: str):
        """Set the environment name to be retrieved."""
        self.env_name = env_name
        """ environment name used for version testing """

    def get_env_in_state(self, state: str = None):
        """Inject an environment into the object."""
        environment = get_environment(self.env_name)
        environment.set_state(state)

        variables = environment.config.load("variables")
        logger.info(
            "%s::%s --> variables: %s",
            self.env_name,
            state,
            json.dumps(variables.get(LOADED_KEY_ROOT), indent=2),
        )

        return environment

    def install(self, environment):
        """Bring up all provisioners as needed."""
        provisioner = environment.fixtures.get_plugin(
            interfaces=[METTA_PLUGIN_INTERFACE_ROLE_PROVISIONER],
        )
        provisioner.prepare()
        try:
            provisioner.apply()
        # pylint: disable=broad-except
        except Exception as err:
            logger.error(
                "Provisioner installation failed.  Tearing down the resources now: %s",
                err,
            )
            self.destroy(environment)
            pytest.exit("Provisioner failed to install")

    def upgrade(self, environment):
        """Upgrade the environment to the second state."""
        provisioner = environment.fixtures.get_plugin(
            interfaces=[METTA_PLUGIN_INTERFACE_ROLE_PROVISIONER],
        )

        try:
            provisioner.apply()
        # pylint: disable=broad-except
        except BaseException:
            logger.error("Provisioner upgrade failed.  Tearing down the resources now")
            self.destroy(environment)
            pytest.exit("Provisioner failed to upgrade")

    # pylint: disable=no-self-use
    def destroy(self, environment):
        """Destroy all created resources."""
        provisioner = environment.fixtures.get_plugin(
            interfaces=[METTA_PLUGIN_INTERFACE_ROLE_PROVISIONER],
        )
        provisioner.destroy()


# This is a base class
# pylint: disable=too-few-public-methods
class TestBase:
    """A collection of reusable tests."""

    __test__ = False

    # this is a base class, to exend test classes easily
    # pylint: disable=no-self-use

    # ----- MKE TESTS ---------------------------------------------------------

    def health(self, environment):
        """Run all of the health checks."""
        health_info: Dict[str, Any] = {}
        """Capture health information for all healthcheck plugins."""

        for health_fixture in self._health_check_fixtures(environment):
            health_plugin = health_fixture.plugin

            try:
                health_plugin_results = health_plugin.health()

            # we turn any exception into a health marker
            # pylint: disable=broad-except
            except Exception as err:
                health_plugin_results = Health(source=health_fixture.instance_id)
                health_plugin_results.critical(str(err))

            health_info[health_fixture.instance_id] = {
                "fixture": {
                    "plugin_id": health_fixture.plugin_id,
                    "instance_id": health_fixture.instance_id,
                    "priority": health_fixture.priority,
                },
                "status": health_plugin_results.status(),
                "messages": list(health_plugin_results.messages()),
            }

            assert health_plugin.status().is_better_than(HealthStatus.ERROR), "HealthCheck Failed"

            return health_info

    def _health_check_fixtures(self, environment) -> Fixtures:
        """Return a Fixtures set of healtchcheck plugins."""
        # get the mke client.
        # We could get this from the launchpad provisioner if we were worried about
        # which mke client plugin instance we receive,  however there is only one
        # in this case.
        return environment.fixtures.filter(
            interfaces=[METTA_PLUGIN_INTERFACE_ROLE_HEALTHCHECK],
        )
