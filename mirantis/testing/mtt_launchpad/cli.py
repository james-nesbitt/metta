import logging
from typing import Dict, Any

import json

from configerus.config import Config
from configerus.plugin import Type

from uctt.cli import CliBase

logger = logging.getLogger('mtt.launchpad.cli')


class LaunchpadCliPlugin(CliBase):

    def fire(self, fixtures: Dict[str, Any]):
        """ return a dict of commands """
        return {
            'config': LaunchpadGroup(fixtures['config'], fixtures['provisioner'])
        }


class LaunchpadGroup():

    def __init__(self, config: Config):
        self.config = config

    def apply(self, label: str, key: str, raw: bool = False):
        """ Retrieve configuration from the config object

        USAGE:

            uctt config get [--raw=True] {label} [{key}]


        """
        try:
            loaded = self.config.load(label)
        except KeyError as e:
            return "Could not find the config label '{}'".format(label)

        try:
            value = loaded.get(key, exception_if_missing=True)
            if raw:
                return value
            else:
                return json.dumps(value)
        except KeyError as e:
            return "Could not find the config key '{}'".format(key)
