"""

Dummy workload plugin.

Dummy workload plugin that really only holds fixtures of its own.  Used for
mocking and testing.

"""
from typing import Dict, Any
import logging

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.fixture import Fixtures

logger = logging.getLogger("metta.contrib.dummy.workload")


# this interface is common for all Metta plugins, but CLI plugins underuse it
# pylint: disable=too-few-public-methods
class DummyWorkloadPlugin:
    """Dummy workload class."""

    def __init__(
        self,
        environment: Environment,
        instance_id: str,
        fixtures: Dict[str, Dict[str, Any]] = None,
    ):
        """Set class properties.

        Parameters:
        -----------
        outputs (Dict[Dict]) : pass in a dictionary which defines outputs that
            should be returned

        clients (Dict[Dict]) : pass in a dictionary which defines which clients
            should be requested when working on a provisioner

        """
        self._environment: Environment = environment
        """ Environemnt in which this plugin exists """
        self._instance_id: str = instance_id
        """ Unique id for this plugin instance """

        self.fixtures = Fixtures()
        """This plugin keeps fixtures."""
        if fixtures is not None:
            for child_instance_id, child_instance_dict in fixtures.items():
                child = environment.add_fixture_from_dict(
                    instance_id=child_instance_id, plugin_dict=child_instance_dict
                )
                self.fixtures.add(child)
