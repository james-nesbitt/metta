"""

Metta workload plugin that polls health in the background.

Polls health periodically in the background and answers health
questions on demand.

"""
import logging
import time
from typing import Dict, Any, List
import threading

from configerus.loaded import LOADED_KEY_ROOT

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.fixtures import Fixtures

from .healthcheck import (
    METTA_PLUGIN_INTERFACE_ROLE_HEALTHCHECK,
    Health,
    HealthStatus,
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
        """Aggregate health per fixture/plugin id. Only ._run() should write to this."""

        self._poll_timings: List[float] = []
        """A list of timestamps to allow separation of messages across polls."""

        self._terminate: bool = False
        """Internal value used to allow an early poll exit."""

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
                    "healthchecks": {"interfaces": [METTA_PLUGIN_INTERFACE_ROLE_HEALTHCHECK]}
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
        if self._thread is None:
            logger.debug("%s Starting health check polling.", self._instance_id)
            self._terminate = False
            self._thread = threading.Thread(name=self._instance_id, target=self._run, args=())
            """Backgroung health poll thread."""
            self._thread.daemon = True  # Daemonize thread
            self._thread.start()  # Start the execution
        else:
            logger.debug("%s Starting health check polling.", self._instance_id)

    def destroy(self):
        """Workload instance interface method to stop the workload."""
        logger.info("Received instructions to terminate polling.")
        self._terminate = True

    def join(self):
        """Join the polling thread and wait until it is done."""
        self._thread.join()

    def _run(self):
        """Periodic poll all healthcheck plugins for health."""
        self._health[self._instance_id] = Health(source=self._instance_id)
        run_start = time.perf_counter()

        try:
            while True:
                if self._terminate:
                    # We have been instructed to stop
                    logger.info("Terminating health poll")
                    break

                poll_start = time.perf_counter()

                if 0 < self.duration < poll_start:
                    # expire the poll if we were given a positive expiry
                    # and if that many seconds have passed.
                    logger.info("health poll expired")
                    break

                # Mark the start of a new poll.
                self._health[self._instance_id].info(
                    f"Polling {self.poll_count()} started, {int(poll_start - run_start)} "
                    "seconds after start"
                )
                # retrieve the health results.
                self._healthcheck()
                # mark another poll complete
                self._poll_timings.append(poll_start)

                poll_stop = time.perf_counter() - run_start
                sleep_dur = ((poll_stop // self.period) + 1) * self.period - poll_stop
                """Duration in secs to the period for the next poll_start."""
                # we may have passed over a period, so we don't just substract and divide
                time.sleep(sleep_dur)

        # Outside of the polling loop, shut everything down

        # pylint: disable=broad-except
        except Exception as err:
            self._reset()
            raise err

        self._reset()

    def _reset(self):
        """Reset the thread of this object."""
        self._thread: threading.Thread = None
        """Thread for polling in case we want to join it."""

        self._health: Dict[str, Health] = {}
        """Aggregate health per fixture/plugin id. Only ._run() should write to this."""

        self._poll_timings: List[float] = []
        """A list of timestamps to allow separation of messages across polls."""

        self._terminate: bool = False
        """Internal value used to allow an early poll exit."""

    def _healthcheck(self) -> Dict[str, Health]:
        """Run a single pass healthcheck on all of the fixtures.

        @TODO make this block so only 1 run can happen at a time.

        Returns:
        --------
        A dict of health plugins per plugin instance_id

        """
        health_info = {}
        for health_fixture in self._healthcheck_fixtures.filter(
            interfaces=[METTA_PLUGIN_INTERFACE_ROLE_HEALTHCHECK]
        ):
            try:
                plugin_health = health_fixture.plugin.health()

            # we turn any exception right into a critical status
            # pylint: disable=broad-except
            except Exception as err:
                plugin_health = Health(source=health_fixture.instance_id)
                plugin_health.critical(
                    f"Health plugin exception [{health_fixture.instance_id}]: {err}"
                )

            plugin_id = health_fixture.plugin_id
            if plugin_id in self._health:
                self._health[plugin_id].merge(plugin_health)
            else:
                self._health[plugin_id] = plugin_health
            health_info[health_fixture.instance_id] = plugin_health
        return health_info

    def health(self) -> Health:
        """Combine all plugin healths into one Health object."""
        agg_health = Health(source=self._instance_id)
        for health in self._health.values():
            agg_health.merge(health)

        if self._terminate:
            agg_health.warning("Healthpoll: not actively polling.")

        return agg_health

    def health_by_source(self) -> Dict[str, Health]:
        """Get the various collected health objects as a Dict."""
        return self._health

    def poll_timing(self, reverse_index: int) -> float:
        """Get the poll timing for a poll index for use with message timing."""
        if len(self._poll_timings) < reverse_index:
            return 0
        return self._poll_timings[-reverse_index]

    def poll_count(self) -> int:
        """Return how many polls have been run."""
        return len(self._poll_timings)


def health_poller_output_log(
    healthpoller: HealthPollWorkload,
    poll_logger,
    period: int,
    count: int,
    exception_on_error: bool = True,
):
    """Periodically log a healthpoller plugins health results and logs.

    This is a usable function which demonstrates a way to interact with an
    active HealthPollWorkload plugin, by periodically asking the plugin for
    updates on health.

    """
    last_message_time = 0
    for i in range(0, count):
        time.sleep(period)

        poll_count = healthpoller.poll_count()
        health = healthpoller.health()
        messages = list(health.messages(since=last_message_time))

        poll_logger.info(
            "HealthCheck %s [%s polls completed] Status: %s [from time %s] ::\n%s",
            i,
            poll_count,
            health.status(),
            int(last_message_time),
            "\n".join(f"-->{message}" for message in messages),
        )
        if len(messages) > 0:
            last_message_time = messages[-1].time

        if exception_on_error:
            assert health.status().is_better_than(HealthStatus.ERROR), "Health was not good"
