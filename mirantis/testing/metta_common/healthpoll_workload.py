"""

Metta workload plugin that polls health in the background.

Polls health periodically in the background and answers health
questions on demand.

"""
import logging
import time
from typing import Dict, Any
import threading

from configerus.loaded import LOADED_KEY_ROOT

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.fixtures import Fixtures
from mirantis.testing.metta.healthcheck import (
    METTA_PLUGIN_INTERFACE_ROLE_HEALTHCHECK,
    Health,
)

logger = logging.getLogger("metta_common.workload.healthpoller")

METTA_PLUGIN_ID_WORKLOAD_HEALTHPOLL = "healthpoll_workload"
"""Output plugin_id for the healthpoller plugin."""

HEALTHPOLL_CONFIG_LABEL = "healthpoll"
"""Default configerus load() label for finding healthpoll configuration."""

HEALTHPOLL_CONFIG_KEY_PERIOD = "poll.period"
"""Configerus key for finding period from config."""
HEALTHPOLL_CONFIG_KEY_DURATION = "poll.duration"
"""Configerus key for finding duration from config."""

HEALTHPOLL_DEFAULT_PERIOD = 30
"""Default value for how frequently to poll health."""
HEALTHPOLL_DEFAULT_DURATION = -1
"""Default value for how may seconds to run the polling for (default to forever)"""

# this is what it takes
# pylint: disable=too-many-instance-attributes
class HealthPollWorkload:
    """Workload plugin that polls health in the background."""

    def __init__(
        self,
        environment: Environment,
        instance_id: str,
        label: str = HEALTHPOLL_CONFIG_LABEL,
        base: Any = LOADED_KEY_ROOT,
    ):
        """Configure the health polls worload plugin instances."""
        self._environment = environment
        self._instance_id = instance_id

        healthpoll_config = environment.config.load(label)

        # make period public and let people tune it live.
        self.period = healthpoll_config.get(
            [base, HEALTHPOLL_CONFIG_KEY_PERIOD], default=HEALTHPOLL_DEFAULT_PERIOD
        )
        """How much time between polls."""
        self.duration = healthpoll_config.get(
            [base, HEALTHPOLL_CONFIG_KEY_DURATION], default=HEALTHPOLL_DEFAULT_DURATION
        )

        self._thread: threading.Thread = None
        """Thread for polling in case we want to join it."""

        self._health: Dict[str, Health] = {}
        """Aggregate health per fixture/plugin id."""

        self._terminate: bool = False
        """Internal value used to allow an early poll exit."""

        self._poll_count = 0
        """How many times have we polled health (might be interesting.)"""

        self._healthcheck_fixtures: Fixtures = None
        """Fixtures list which should be searched for healthcheck fixtures."""

    # deep argument is an info() standard across plugins
    # pylint: disable=unused-argument
    def info(self, deep: bool = False):
        """Return dict data about this plugin for introspection."""
        return {
            "workload": {
                "configuration": {"period": self.period, "duration": self.duration},
                "required_fixtures": {
                    "healthchecks": {
                        "interfaces": [METTA_PLUGIN_INTERFACE_ROLE_HEALTHCHECK]
                    }
                },
            }
        }

    def prepare(self, fixtures: Fixtures = None):
        """Create a workload instance from a set of fixtures.

        Parameters:
        -----------
        fixtures (Fixtures) : a set of fixtures that this workload will use to
            retrieve a docker client plugin.

        """
        if fixtures is None:
            fixtures = self._environment.fixtures

        self._healthcheck_fixtures = fixtures

    def apply(self):
        """Start polling healthchecks and keep a status."""
        thread = threading.Thread(name=self._instance_id, target=self._run, args=())
        """Backgroung health poll thread."""
        thread.daemon = True  # Daemonize thread
        thread.start()  # Start the execution
        self._thread = thread

    def destroy(self):
        """Workload instance interface method to stop the workload."""
        self._terminate = True

    def join(self):
        """Join the polling thread and wait until it is done."""
        self._thread.join()

    def _run(self):
        """Periodic poll all healthcheck plugins for health."""
        run_start = time.perf_counter()
        while True:
            if self._terminate:
                # We have been instructed to stop
                logger.info("terminating health poll")
                break

            poll_start = time.perf_counter() - run_start

            if 0 < self.duration < poll_start:
                # expire the poll if we were given a positive expiry
                # and if that many seconds have passed.
                logger.info("health poll expired")
                break

            self._poll_count += 1
            for plugin_id, plugin_health in self._healthcheck().items():
                if hasattr(self._health, plugin_id):
                    self._health[plugin_id].merge(plugin_health)
                else:
                    self._health[plugin_id] = plugin_health

            poll_stop = time.perf_counter() - run_start
            sleep_dur = ((poll_stop // self.period) + 1) * self.period - poll_stop
            """Duration in secs to the period for the next poll_start."""
            # we may have passed over a period, so we don't just substract and divide
            time.sleep(sleep_dur)

        print("ended")

    def _healthcheck(self) -> Dict[str, Health]:
        """Run a single pass healthcheck on all of the fixtures."""
        health_info = {}
        for health_fixture in self._healthcheck_fixtures.filter(
            interfaces=[METTA_PLUGIN_INTERFACE_ROLE_HEALTHCHECK]
        ):
            try:
                plugin_health = health_fixture.plugin.health()

            # we turn any exception right into a critical status
            # pylint: disable=broad-except
            except Exception as err:
                plugin_health = Health()
                plugin_health.critical(
                    f"Health plugin exception [{health_fixture.instance_id}]: {err}"
                )

            health_info[health_fixture.instance_id] = plugin_health
        return health_info

    def health(self) -> Health:
        """Combine all plugin healths into one Health object."""
        agg_health = Health()
        for health in self._health.values():
            agg_health.merge(health)
        return agg_health

    def poll_count(self) -> int:
        """Return how many polls have been run."""
        return self._poll_count
