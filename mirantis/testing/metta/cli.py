"""

CLI Plugins base

@see ./cli for the cli implementation

"""
import logging

import mirantis.testing.metta
from mirantis.testing.metta.plugin import METTAPlugin, Type

logger = logging.getLogger('metta.cli')

METTA_PLUGIN_TYPE_CLI = Type.CLI
""" Fast access to the output plugin type """


class CliBase(METTAPlugin):
    """ Base class for cli plugins """
    pass

    def exec(self):
        """ this plugin can execute """
        raise NotImplemented("this functionality has not yet been written.")
