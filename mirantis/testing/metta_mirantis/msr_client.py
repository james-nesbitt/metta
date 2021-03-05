"""

Mirantis MSR API Client

"""

import logging

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.client import ClientBase

logger = logging.getLogger('metta.contrib.metta_mirantis.client.msrapi')


class MSRAPIClientPlugin(ClientBase):
    """ Client for API Connections to MSR """

    def __init__(self, environment: Environment,
                 instance_id: str):
        """

        Parameters:
        -----------


        """
        ClientBase.__init__(self, environment, instance_id)
