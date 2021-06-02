"""

PLUGIN: Output.

Workload plugins use clients to apply workloads to a testing system.  The
system is irrelevant tothe workload plugin, as it only cares whether or not it
can retrieve the expected clients.

Workload clients are expected to allow creation of Workload instances from
clients, so that multiple applications of the workload can be managed at one
time.

"""

import logging

from .fixtures import Fixtures

logger = logging.getLogger('metta.workload')

METTA_PLUGIN_TYPE_WORKLOAD = "workload"
""" Fast access to the workload type """

METTA_WORKLOAD_CONFIG_WORKLOADS_LABEL = 'workloads'
""" A centralized configerus load label for multiple workloads """
METTA_WORKLOAD_CONFIG_WORKLOAD_LABEL = 'workload'
""" A centralized configerus load label for a workload """
METTA_WORKLOAD_CONFIG_WORKLOADS_KEY = 'workloads'
""" A centralized configerus key for multiple workloads """
METTA_WORKLOAD_CONFIG_WORKLOAD_KEY = 'workload'
""" A centralized configerus key for one workload """


# pylint: disable=too-few-public-methods
class WorkloadBase:
    """Base class for workload plugins."""

    def create_instance(self, fixtures: Fixtures) -> 'WorkloadInstanceBase':
        """Create a workload instance from a set of fixtures."""


class WorkloadInstanceBase:
    """An instance of a running workload."""

    def apply(self):
        """Run the workload.

        @NOTE Needs a kubernetes client fixture to run.
              Use .set_fixtures() first

        """
        raise NotImplementedError(
            "This workload plugin has not implemented apply()")

    def destroy(self):
        """Destroy any created resources."""
        raise NotImplementedError(
            "This workload plugin has not implemented destroy()")
