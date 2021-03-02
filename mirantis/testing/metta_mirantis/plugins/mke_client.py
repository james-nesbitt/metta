"""

Mirantis MKE API Client

"""

import logging

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.client import ClientBase

logger = logging.getLogger('metta.contrib.metta_mirantis.client.mkeapi')


class MKEAPIClientPlugin(ClientBase):
    """ Client for API Connections to MKE """

    def __init__(self, environment: Environment,
                 instance_id: str):
        """

        Parameters:
        -----------


        """
        ClientBase.__init__(self, environment, instance_id)
