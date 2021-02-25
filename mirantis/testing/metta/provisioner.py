"""

Provisioning

"""

import logging

from configerus.config import Config
from configerus.loaded import LOADED_KEY_ROOT

from .plugin import METTAPlugin, Type
from .fixtures import Fixtures

logger = logging.getLogger('metta.provisioner')

METTA_PLUGIN_TYPE_PROVISIONER = Type.PROVISIONER
""" Fast access to the Provisioner plugin_id """

METTA_PROVISIONER_CONFIG_PROVISIONERS_LABEL = 'provisioners'
""" A centralized configerus load labe for multiple provisioners """
METTA_PROVISIONER_CONFIG_PROVISIONER_LABEL = 'provisioner'
""" A centralized configerus load label a provisioner """
METTA_PROVISIONER_CONFIG_PROVISIONERS_KEY = 'provisioners'
""" A centralized configerus key for multiple provisioners """
METTA_PROVISIONER_CONFIG_PROVISIONER_KEY = 'provisioner'
""" A centralized configerus key for one provisioner """


class ProvisionerBase(METTAPlugin):
    "Base Provisioner plugin class"

    def prepare(self, label: str = '', base: str = ''):
        """ Prepare the provisioner to apply resources

        Initial Provisioner plugin is expected to be of very low cost until
        prepare() is executed.  At this point the plugin should load any config
        and perform any validations needed.
        The plugin should not create any resources but it is understood that
        there may be a cost of preparation.

        Provisioners are expected to load a lot of config to self-program.
        Because of this, they allow passing of a configerus label for .load()
        and a base for .get() in case there is an alterante config source
        desired.

        """
        raise NotImplementedError(
            'This provisioner has not yet implemented prepare')

    def apply(self):
        """ bring a cluster to the configured state """
        raise NotImplementedError(
            'This provisioner has not yet implemented apply')

    def destroy(self):
        """ remove all resources created for the cluster """
        raise NotImplementedError(
            'This provisioner has not yet implemented destroy')
