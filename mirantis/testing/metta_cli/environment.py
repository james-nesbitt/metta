import logging
from typing import Dict, Any

import json

from mirantis.testing.metta import environment_names
from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.cli import CliBase

logger = logging.getLogger('metta.cli.environment')


class EnvironmentCliPlugin(CliBase):

    def fire(self):
        """ return a dict of commands """
        return {
            'environment': EnvironmentGroup(self.environment)
        }


class EnvironmentGroup():

    def __init__(self, environment: Environment):
        self.environment = environment

    def names(self, raw: bool = False):
        """ List all of the environment names  """
        names = environment_names()
        if raw:
            return names
        else:
            return json.dumps(names)
