"""

Metta client for itneracting with plugin health checks.

"""
import logging
from typing import Dict, Any, Generator

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.fixtures import Fixtures, Fixture

from .healthcheck import (
    METTA_PLUGIN_INTERFACE_ROLE_HEALTHCHECK,
    Health,
)


logger = logging.getLogger("health:client")


METTA_HEALTH_CLIENT_PLUGIN_ID = "metta_health_client"
""" health client plugin id """


class HealthClientPlugin:
    """Metta terraform client."""

    # pylint: disable=too-many-arguments
    def __init__(self, environment: Environment, instance_id: str):
        """Initial client configuration."""
        self._environment = environment
        """ Environemnt in which this plugin exists """
        self._instance_id = instance_id
        """ Unique id for this plugin instance """

    # deep argument is an info() standard across plugins
    # pylint: disable=unused-argument
    def info(self, deep: bool = False) -> Dict[str, Any]:
        """Return dict data about this plugin for introspection."""
        return {"fixtures": list(fixture.info(deep=deep) for fixture in self.health_fixtures())}

    def health(self) -> Health:
        """Check all health plugin response.

        Returns:
        --------
        A Health object that aggregates all available health responses.

        """
        agg_health: Health = Health(source=self._instance_id)
        """Start a top level aggregate health object."""

        for fixture_health in self.healths():
            agg_health.merge(fixture_health)

        return agg_health

    def healths(self) -> Generator[Health, None, None]:
        """Check all health plugin response.

        Returns:
        --------
        A Dict of Health objects keyed on source plugins.

        """

        def safe_health(fixture: Fixture) -> Health:
            try:
                return fixture.plugin.health()

            # pylint: disable=broad-except
            except Exception as err:
                health: Health = Health(source=fixture.instance_id)
                health.critical(str(err))
                return health

        return (safe_health(fixture) for fixture in self.health_fixtures())

    def health_fixtures(self) -> Fixtures:
        """Get the fixtures that can provide health check."""
        return self._environment.fixtures.filter(
            interfaces=[METTA_PLUGIN_INTERFACE_ROLE_HEALTHCHECK]
        )
