"""

Dummy workload plugin

"""

import logging
from mirantis.testing.mtt.workload import WorkloadBase

logger = logging.getLogger('mirantis.testing.mtt_dummy.workload')

class DummyWorkloadPlugin(WorkloadBase):
    """ Dummy workload class """
