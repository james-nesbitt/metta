"""

Health check plugins

Plugins which can be used to determine health of a system.

The usecase for healthchecks is that any functionality can
be added to an environment, and as a collection they can be
used to approve of the health of a system.

Any running component such as a provisioner, a client, or
a workload can be used to provide a health-check plugin so
that a wholistic health check can be run.

"""
from enum import Enum
import time
from typing import List
import logging


logger = logging.getLogger("healthcheck")

METTA_PLUGIN_INTERFACE_ROLE_HEALTHCHECK = "healthcheck"
""" metta plugin interface identifier for healthcheck plugins """

METTA_HEALTHCHECK_CONFIG_HEALTHCHECKS_LABEL = "healthchecks"
""" A centralized configerus load label for multiple healthchecks """
METTA_HEALTHCHECK_CONFIG_HEALTHCHECK_LABEL = "healthcheck"
""" A centralized configerus load label for an healthcheck """
METTA_HEALTHCHECK_CONFIG_HEALTHCHECKS_KEY = "healthchecks"
""" A centralized configerus key for multiple healthchecks """
METTA_HEALTHCHECK_CONFIG_HEALTHCHECK_KEY = "healthcheck"
""" A centralized configerus key for one healthcheck """


class HealthStatus(Enum):
    """Status indicator.

    Numerically ordered, with larger value being less healthy (worse)

    Typically anything lower than 3 is still healthy, but -1 means that
    no information is available yet.

    """

    # no health information is availale
    UNKNOWN = -1
    # just an informational state
    INFO = 0
    # No health issues have been discovered
    HEALTHY = 3
    # There are some health warnings but no operational defects.
    WARNING = 5
    # Some health errors have been detected
    ERROR = 7
    # Significant health concerns exist.
    CRITICAL = 10

    def is_better_than(self, than: "HealthStatus"):
        """Return boolean if the passed status is worse."""
        assert isinstance(than, HealthStatus), f"Poor argument provided: {than}"
        return self.value < than.value


def worse_health_status(first: "HealthStatus", second: "HealthStatus") -> "HealthStatus":
    """Return the worst health status between two."""
    assert isinstance(first, HealthStatus), f"Poor argument provided: first {first}"
    assert isinstance(second, HealthStatus), f"Poor argument provided: second {second}"

    if first.is_better_than(second):
        return second
    return first


# yes this is a struct
# pylint: disable=too-few-public-methods
class HealthMessage:
    """A message status combination."""

    def __init__(self, source: str, status: HealthStatus, message: str):
        """Create a new message with status value."""
        self.time: float = time.perf_counter()
        self.source: str = source
        self.status: HealthStatus = status
        self.message: str = message

    def __str__(self) -> str:
        """Convert message instance to string."""
        return f"[{int(self.time)}] {self.source}: {self.status} => {self.message}"


class Health:
    """Health status.

    A temporal health statement, typically generated by a health
    check plugin.

    """

    def __init__(self, source: str = "", status: HealthStatus = HealthStatus.UNKNOWN):
        """Health constructor."""
        self.source: str = source
        """Source producer identity of this health object."""
        self._status: HealthStatus = status
        """Health status for this health object."""
        self._messages: List[HealthMessage] = []

    def merge(self, target: "Health"):
        """Combine another HealtStatus into the current one."""
        assert isinstance(target, Health)
        self._status = worse_health_status(self.status(), target.status())
        self._messages.extend(target.messages())
        self._messages.sort(key=lambda x: x.time)

    def status(self) -> HealthStatus:
        """Return the status."""
        return self._status

    def messages(self, source: str = "", since: int = 0) -> List[HealthMessage]:
        """Return filtered health messages."""
        return (
            message
            for message in self._messages
            if source in ["", message.source] and (since == 0 or message.time > since)
        )

    # Health message recording

    def new_message(self, status: HealthStatus, message: str):
        """Add a message of status INFO."""
        self._messages.append(HealthMessage(source=self.source, status=status, message=message))
        self._status = worse_health_status(self._status, status)

    def unknown(self, message: str):
        """Add a message of status HEALTHY."""
        self.new_message(status=HealthStatus.UNKNOWN, message=message)

    def info(self, message: str):
        """Add a message of status HEALTHY."""
        self.new_message(status=HealthStatus.INFO, message=message)

    def healthy(self, message: str):
        """Add a message of status HEALTHY."""
        self.new_message(status=HealthStatus.HEALTHY, message=message)

    def warning(self, message: str):
        """Add a message of status WARNING."""
        self.new_message(status=HealthStatus.WARNING, message=message)

    def error(self, message: str):
        """Add a message of status ERROR."""
        self.new_message(status=HealthStatus.ERROR, message=message)

    def critical(self, message: str):
        """Add a message of status ERROR."""
        self.new_message(status=HealthStatus.CRITICAL, message=message)
