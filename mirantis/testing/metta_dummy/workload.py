"""

Dummy workload plugin.

Dummy workload plugin that really only holds fixtures of its own.  Used for
mocking and testing.

"""
from typing import Dict, Any
import logging

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.fixtures import Fixtures

logger = logging.getLogger('metta.contrib.dummy.workload')


# this interface is common for all Metta plugins, but CLI plugins underuse it
# pylint: disable=too-few-public-methods
class DummyWorkloadPlugin:
    """Dummy workload class."""

    def __init__(self, environment: Environment, instance_id: str,
                 fixtures: Dict[str, Dict[str, Any]] = None):
        """Set class properties.

        Parameters:
        -----------
        outputs (Dict[Dict]) : pass in a dictionary which defines outputs that
            should be returned

        clients (Dict[Dict]) : pass in a dictionary which defines which clients
            should be requested when working on a provisioner

        """
        self.environment = environment
        """ Environemnt in which this plugin exists """
        self.instance_id = instance_id
        """ Unique id for this plugin instance """

        if fixtures is not None:
            fixtures = environment.add_fixtures_from_dict(plugin_list=fixtures)
        else:
            fixtures = Fixtures()
        self.fixtures: Fixtures = fixtures
        """ All fixtures added to this dummy plugin. """
