"""

Dummy client plugin

"""

import logging
from typing import Dict, Any

from mirantis.testing.metta.plugin import Type
from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.client import ClientBase
from mirantis.testing.metta.fixtures import UCCTFixturesPlugin

logger = logging.getLogger('metta.contrib.dummy.client')


class DummyClientPlugin(ClientBase, UCCTFixturesPlugin):
    """ Dummy client class

    As with all dummies, this is a failsafe plugin, that should never throw any
    exceptions if used according to metta standards.

    It can be used as a placeholder during development, or it can be used to
    log client events and output for greater development and debugging.

    The client will log any method call, including unknown methods, and so it
    can be used in place of any client, if you don't need the methods to return
    anything
    """

    def __init__(self, environment: Environment, instance_id: str,
                 fixtures: Dict[str, Dict[str, Any]] = {}):
        """ Run the super constructor but also set class properties

        Overrides the ClientBase.__init__

        Arguments:
        ----------

        environment (metta.environment.Environment) : Environment in which this
            plugin exists.

        instance_id (str) : unique identifier for this plugin instance.

        fixtures (dict) : You can pass in some fixture definitions which this
            class will turn into fixtures and make retrievable.  This is a big
            part of the dummy.

        """
        ClientBase.__init__(self, environment, instance_id)

        fixtures = environment.add_fixtures_from_dict(plugin_list=fixtures)
        """ All fixtures added to this dummy plugin. """
        UCCTFixturesPlugin.__init__(self, fixtures)
