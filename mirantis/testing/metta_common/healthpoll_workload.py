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
from mirantis.testing.metta.healthcheck import METTA_PLUGIN_TYPE_HEALTHCHECK, Health

logger = logging.getLogger("metta.contrib.common.output.dict")

METTA_PLUGIN_ID_WORKLOAD_HEALTHPOLL = "healthpoll"
""" output plugin_id for the dict plugin """

WORKLOAD_HEALTHPOLL_CONFIG_LABEL = "healthpoll"
"""Default configerus load() label for finding healthpoll configuration."""


class HealthPollWorkload:
    """workload plugin that polls health in the background."""

    def __init__(
        self,
        environment: Environment,
        instance_id: str,
        label: str = WORKLOAD_HEALTHPOLL_CONFIG_LABEL,
        base: Any = LOADED_KEY_ROOT,
    ):
        """Configure the health polls worload plugin instances."""
        self.environment = environment
        self.instance_id = instance_id

        healthpoll_config = environment.config.load(label)

        self.period = healthpoll_config.get("poll.period", default=30)
        """How much time between polls."""
        self.duration = healthpoll_config.get("poll.duration", default=3600)

    def create_instance(self, fixtures: Fixtures):
        """Create a workload instance from a set of fixtures.

        Parameters:
        -----------
        fixtures (Fixtures) : a set of fixtures that this workload will use to
            retrieve a docker client plugin.

        """
        healthcheck_fixtures = fixtures.filter(
            plugin_type=METTA_PLUGIN_TYPE_HEALTHCHECK
        )

        return HealthCheckPollWorkloadInstance(
            name=f"{self.instance_id}-instance",
            fixtures=healthcheck_fixtures,
            period_secs=self.period,
            expire_secs=self.duration,
        )

    def info(self):
        """Return dict data about this plugin for introspection."""
        return {
            "workload": {
                "fixture": {"instance_id": self.instance_id},
                "configuration": {"period": self.period, "duration": self.duration},
                "required_fixtures": {
                    "healthchecks": {"plugin_type": METTA_PLUGIN_TYPE_HEALTHCHECK}
                },
            }
        }


class HealthCheckPollWorkloadInstance:
    """Workload instance which starts polling health in the background."""

    def __init__(
        self,
        name: str,
        fixtures: Fixtures,
        period_secs: int = 10,
        expire_secs: int = -1,
    ):
        """Start polling healthchecks and keep a status.

        Parameters:
        -----------
        name (str) : String used to name the polling thread
        fixture (Fixtures) : fixture set, all healtcheck fixtures will
            be polled for health.

        period_secs (int) : period in seconds between polls
        expire_secs (int) : after this many secs polling will stop, Use
            -1 to indicate no expiry.

        """
        self.name = name
        """Keep the string name."""
        self.fixtures: Fixtures = fixtures.filter(
            plugin_type=METTA_PLUGIN_TYPE_HEALTHCHECK
        )
        """Set of healtcheck fixtures to be polled for health."""
        self.health: Dict[str, Health] = {}
        """Aggregate health per fixture/plugin id."""

        self.terminate: bool = False
        """Internal value used to allow an early poll exit."""

        self.poll_count = 0
        """How many times have we polled health (might be interesting.)"""

        thread = threading.Thread(
            name=name, target=self._run, args=(period_secs, expire_secs)
        )
        """Backgroung health poll thread."""
        thread.daemon = True  # Daemonize thread
        thread.start()  # Start the execution
        self.thread = thread

    def _run(self, period: int, expire: int):
        """Periodic poll all healthcheck plugins for health."""
        run_start = time.perf_counter()
        while True:
            if self.terminate:
                # We have been instructed to stop
                logger.info("terminating health poll")
                break

            poll_start = time.perf_counter() - run_start

            if 0 < expire < poll_start:
                # expire the poll if we were given a positive expiry
                # and if that many seconds have passed.
                logger.info(f"health poll expired")
                break

            self.poll_count += 1
            for plugin_id, plugin_health in self.healthcheck().items():
                if hasattr(self.health, plugin_id):
                    self.health[plugin_id].merge(plugin_health)
                else:
                    self.health[plugin_id] = plugin_health

            poll_stop = time.perf_counter() - run_start
            sleep_dur = ((poll_stop // period) + 1) * period - poll_stop
            """Duration in secs to the period for the next poll_start."""
            # we may have passed over a period, so we don't just substract and divide
            time.sleep(sleep_dur)

        print("ended")

    def join(self):
        """Join the polling thread and wait until it is done."""
        self.thread.join()

    def healthcheck(self) -> Dict[str, Health]:
        """Run a single pass healthcheck on all of the fixtures."""
        health_info = {}
        for health_fixture in self.fixtures:
            try:
                plugin_health = health_fixture.plugin.health()

            # we turn any exception right into a critical status
            # pylint: disable=broad-except
            except Exception as err:
                plugin_health = Health()
                plugin_health.critical(f"Health plugin exception: {err}")

            health_info[health_fixture.instance_id] = plugin_health
        return health_info

    def health_aggregate(self) -> Health:
        """Combine all plugin healths into one Health object."""
        agg_health = Health()
        for health in self.health.values():
            agg_health.merge(health)
        return agg_health

    def stop(self):
        """Tell the polling thread to stop before its next poll."""
        self.terminate = True
