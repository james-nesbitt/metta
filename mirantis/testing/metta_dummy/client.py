"""

Dummy client plugin

"""

import logging
from typing import Dict, Any

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.fixture import Fixtures

logger = logging.getLogger("metta.contrib.dummy.client")


# this interface is common for all Metta plugins, but CLI plugins underuse it
# pylint: disable=too-few-public-methods
class DummyClientPlugin:
    """Dummy client class

    As with all dummies, this is a failsafe plugin, that should never throw any
    exceptions if used according to metta standards.

    It can be used as a placeholder during development, or it can be used to
    log client events and output for greater development and debugging.

    The client will log any method call, including unknown methods, and so it
    can be used in place of any client, if you don't need the methods to return
    anything
    """

    def __init__(
        self,
        environment: Environment,
        instance_id: str,
        fixtures: Dict[str, Dict[str, Any]] = None,
    ):
        """Sset class properties

        Arguments:
        ----------

        environment (Environment) : Environment in which thisplugin exists.

        instance_id (str) : unique identifier for this plugin instance.

        fixtures (dict) : You can pass in some fixture definitions which this
            class will turn into fixtures and make retrievable.  This is a big
            part of the dummy.

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
