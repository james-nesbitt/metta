import logging

from configerus.config import Config

from .plugin import METTAPlugin, Type
from .fixtures import Fixtures

logger = logging.getLogger('metta.workload')

METTA_PLUGIN_ID_WORKLOAD = Type.WORKLOAD
""" Fast access to the workload type """

METTA_WORKLOAD_CONFIG_WORKLOADS_LABEL = 'workloads'
""" A centralized configerus load label for multiple workloads """
METTA_WORKLOAD_CONFIG_WORKLOAD_LABEL = 'workload'
""" A centralized configerus load label for a workload """
METTA_WORKLOAD_CONFIG_WORKLOADS_KEY = 'workloads'
""" A centralized configerus key for multiple workloads """
METTA_WORKLOAD_CONFIG_WORKLOAD_KEY = 'workload'
""" A centralized configerus key for one workload """


class WorkloadBase(METTAPlugin):
    """ Base class for workload plugins """

    def create_instance(self, fixtures: Fixtures) -> 'WorkloadInstanceBase':
        """ createe a workload instance from a set of fixtures """


class WorkloadInstanceBase:
    """ An instance of a running workload """

    def apply(self):
        """ Run the workload

        @NOTE Needs a kubernetes client fixture to run.  Use .set_fixtures() first

        """
        raise NotImplementedError(
            "This workload plugin has not implemented apply()")

    def destroy(self):
        """ destroy any created resources """
        raise NotImplementedError(
            "This workload plugin has not implemented destroy()")
