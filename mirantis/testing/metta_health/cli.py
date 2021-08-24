"""

Metta cli plugin for the healthpoll workload.

Metta cli handling and interacting with a healthpoll workload.

"""
from typing import Dict, Any
import time

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.fixture import Fixture
from mirantis.testing.metta_cli.base import CliBase, cli_output

from .healthcheck import Health, HealthStatus
from .health_client import METTA_HEALTH_CLIENT_PLUGIN_ID
from .healthpoll_workload import METTA_PLUGIN_ID_WORKLOAD_HEALTHPOLL

METTA_PLUGIN_ID_HEALTH_CLI = "healthcli"
""" Mirantis Health CLI plugin id """


# this interface is common for all Metta plugins, but CLI plugins underuse it
# pylint: disable=too-few-public-methods


# this interface is common for all Metta plugins, but CLI plugins underuse it
# pylint: disable=too-few-public-methods
class HealthCliPlugin(CliBase):
    """Fire command/group generator for healthcheck commands."""

    def fire(self):
        """Return a dict of commands."""
        if (
            len(
                self._environment.fixtures().filter(
                    plugin_id=METTA_HEALTH_CLIENT_PLUGIN_ID,
                    exception_if_missing=False,
                )
            )
            > 0
        ):
            return {"health": HealthcheckClientGroup(self._environment)}

        return {}


def _fixture_health_output(fixture: Fixture, verbosity: HealthStatus = None) -> Dict[str, Any]:
    """Run Helper to run a fixture's health function and create cli output."""
    health: Health = fixture.plugin.health()

    fixture_health_info = {
        "fixture": {
            "plugin_id": fixture.plugin_id,
            "instance_id": fixture.instance_id,
            "priority": fixture.priority,
        },
        "status": health.status(),
    }
    messages = list(health.messages(verbosity=verbosity))
    if len(messages) > 0:
        fixture_health_info["messages"] = messages
    return fixture_health_info


class HealthcheckClientGroup:
    """Health client commands."""

    def __init__(self, environment: Environment):
        """Create CLI command group."""
        self._environment: Environment = environment

        if (
            len(
                self._environment.fixtures().filter(
                    plugin_id=METTA_PLUGIN_ID_WORKLOAD_HEALTHPOLL,
                    exception_if_missing=False,
                )
            )
            > 0
        ):
            self.healthpoll = HealthpollWorkloadGroup(self._environment)

    def _select_client(self, instance_id: str = ""):
        """Pick a matching client."""
        if instance_id:
            return self._environment.fixtures().get(
                plugin_id=[METTA_HEALTH_CLIENT_PLUGIN_ID],
                instance_id=instance_id,
            )

        # Get the highest priority provisioner
        return self._environment.fixtures().get(
            plugin_id=METTA_HEALTH_CLIENT_PLUGIN_ID,
        )

    def info(self, client: str = "", deep: bool = False):
        """Get info about a client plugin."""
        healthclient_fixture = self._select_client(instance_id=client)
        return cli_output(healthclient_fixture.info(deep=deep))

    def list(self, client: str = "", deep: bool = False):
        """List all healthchecks."""
        healthclient_plugin = self._select_client(instance_id=client).plugin
        return cli_output(healthclient_plugin.health_fixtures().info(deep=deep))

    def check(self, verbosity: str = "", client: str = ""):
        """Output health status of healthchecks."""
        fixture = self._select_client(instance_id=client)
        verbosity_status = HealthStatus[verbosity.upper()] if verbosity else None

        # return a single aggregate health object
        return cli_output(_fixture_health_output(fixture, verbosity=verbosity_status))

    def checks(self, verbosity: str = "", client: str = ""):
        """Output health status of healthchecks per plugin."""
        fixture = self._select_client(instance_id=client)
        verbosity_status = HealthStatus[verbosity.upper()] if verbosity else None

        # return a dict of healtchecks per plugin instance_id
        return cli_output(
            {
                fixture.instance_id: _fixture_health_output(fixture, verbosity=verbosity_status)
                for fixture in fixture.plugin.health_fixtures()
            }
        )

    def check_plugin(self, instance_id: str, client: str = ""):
        """Output health status of a specific fixture/plugin."""
        # Health Client plugin for asking health questions.
        healthclient_plugin = self._select_client(instance_id=client).plugin
        # Speific plugin to check.
        fixture = healthclient_plugin.health_fixtures().get(instance_id=instance_id)
        return cli_output(fixture)

    def poll(self, period: int = 15, verbosity: str = "", client: str = ""):
        """Poll health periodically."""
        health_client_fixture = self._select_client(instance_id=client)
        verbosity_status = HealthStatus[verbosity.upper()] if verbosity else None
        iteration = 0
        while True:
            for fixture in health_client_fixture.plugin.health_fixtures():
                print(f"[{iteration}] {fixture.instance_id} -->")
                print(_fixture_health_output(fixture=fixture, verbosity=verbosity_status))
            time.sleep(period)


class HealthpollWorkloadGroup:
    """HealthPolling workload CLI commands."""

    def __init__(self, environment: Environment):
        """Create new cli group object."""
        self._environment: Environment = environment

    def _select_fixture(self, instance_id: str = ""):
        """Pick a matching fixture in case there are more than one."""
        if instance_id:
            return self._environment.fixtures().get(
                plugin_id=METTA_PLUGIN_ID_WORKLOAD_HEALTHPOLL,
                instance_id=instance_id,
            )

        # Get the highest priority fixture
        return self._environment.fixtures().get(
            plugin_id=METTA_PLUGIN_ID_WORKLOAD_HEALTHPOLL,
        )

    def info(self, instance_id: str = "", deep: bool = False, children: bool = True):
        """Get info about a plugin."""
        fixture = self._select_fixture(instance_id=instance_id)
        return cli_output(fixture.info(deep=deep, children=children))

    # protected method is used for introspection and testing.
    # pylint: disable=protected-access
    def health(self, instance_id: str = ""):
        """Return the current health from the healthpoller."""
        fixture = self._select_fixture(instance_id=instance_id)
        plugin = fixture.plugin

        plugin.prepare(self._environment.fixtures())
        healths = plugin._healthcheck()

        health_info = {}
        for health_id, health in healths.items():
            health_info[health_id] = {
                "status": health.status(),
                "message": list(health.messages(0)),
            }

        return cli_output(health_info)

    def poll(self, instance_id: str = "", period: int = 10):
        """Return the current health from the healthpoller."""
        fixture = self._select_fixture(instance_id=instance_id)
        plugin = fixture.plugin

        plugin.prepare(self._environment.fixtures())
        plugin.apply()
        time.sleep(5)

        i = 0
        last_message_time = 0
        while True:
            i += 1
            health = plugin.health()
            messages = list(health.messages(since=last_message_time))

            print(
                cli_output(
                    {
                        "poll_count": plugin.poll_count(),
                        "status": health.status(),
                        "messages": {
                            "since": int(last_message_time),
                            "items": messages,
                        },
                    }
                )
            )

            # next round we won't include many repeat messages
            if len(messages) > 0:
                last_message_time = max(message.time for message in messages)

            time.sleep(period)
