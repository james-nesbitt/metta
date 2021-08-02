"""

Metta cli plugin for the healthpoll workload.

Metta cli handling and interacting with a healthpoll workload.

"""

import time

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta_cli.base import CliBase, cli_output

from .healthpoll_workload import METTA_PLUGIN_ID_WORKLOAD_HEALTHPOLL

METTA_PLUGIN_ID_CLI_HEALTHPOLL = "healthpoll_cli"
""" Mirantis Healthpoll CLI plugin id """


# this interface is common for all Metta plugins, but CLI plugins underuse it
# pylint: disable=too-few-public-methods


class HealthpollCliPlugin(CliBase):
    """Metta CLI plugin which injects the healthPolling workload CLI commands."""

    def fire(self):
        """Return a dict of commands for healthPolling workloads."""
        if (
            len(
                self._environment.fixtures.filter(
                    plugin_id=METTA_PLUGIN_ID_WORKLOAD_HEALTHPOLL,
                    exception_if_missing=False,
                )
            )
            > 0
        ):

            return {"healthpoll": HealthpollCliGroup(self._environment)}

        return {}


class HealthpollCliGroup:
    """HealthPolling workload CLI commands."""

    def __init__(self, environment: Environment):
        """Create new cli group object."""
        self._environment = environment

    def _select_fixture(self, instance_id: str = ""):
        """Pick a matching fixture in case there are more than one."""
        if instance_id:
            return self._environment.fixtures.get(
                plugin_id=METTA_PLUGIN_ID_WORKLOAD_HEALTHPOLL,
                instance_id=instance_id,
            )

        # Get the highest priority fixture
        return self._environment.fixtures.get(
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

        plugin.prepare(self._environment.fixtures)
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

        plugin.prepare(self._environment.fixtures)
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
