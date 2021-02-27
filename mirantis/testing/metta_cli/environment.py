import logging
from typing import Dict, Any

import json

from mirantis.testing.metta import environment_names, get_environment
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

    def _environment(self, environment: str = ''):
        """ select an environment """
        if not environment:
            return self.environment
        return get_environment(environment)

    def name(self, environment: str = ''):
        """ return env name """
        environment = self._environment(environment)
        return environment.name

    def bootstraps(self, environment: str = ''):
        """ List bootstraps that have been applied to the environment """
        environment = self._environment(environment)

        list = [bootstrap for bootstrap in environment.bootstrapped]

        return json.dumps(list, indent=2, default=lambda X: "{}".format(X))
