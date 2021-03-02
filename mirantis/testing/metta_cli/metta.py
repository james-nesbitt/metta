import logging
import json
from typing import Dict, Any
import inspect

from mirantis.testing.metta.plugin import Factory
from mirantis.testing.metta.cli import CliBase

logger = logging.getLogger('metta.cli.metta')


class MettaCliPlugin(CliBase):
    """ metta Cli info plugin

    """

    def fire(self):
        """ return a dict of commands """
        return {
            'metta': MettaCoreCli()
        }


class MettaCoreCli:
    """ Interact with the metta core """

    def hello(self, raw: bool = True):
        """ sanity test on bootstrap """
        return "Hello World, I was able to bootstrap"

    def plugins(self):
        """ List plugins that have been registered with the environment """

        list = {}
        for type in Factory.registry:
            list[type] = []
            for plugin_id in Factory.registry[type]:
                list[type].append(plugin_id)

        return json.dumps(list, indent=2, default=lambda X: "{}".format(X))
