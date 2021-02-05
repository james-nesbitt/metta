"""

Dummy MTT provisioner plugin

"""

import logging

from mirantis.testing.mtt.provisioner import ProvisionerBase

logger = logging.getLogger('mirantis.testing.mtt_dummy.provisioner')

class DummyProvisionerPlugin(ProvisionerBase):
    """ Dummy provisioner class """

    def prepare(self):
        """ Pretend to prepare the provisioner """

    def apply(self):
        """ pretend to bring a cluster up """
        pass

    def destroy(self):
        """ pretend to brind a cluster down """
        pass

    def get_output(self, name:str):
        """ Retrieve a dummy output """
        pass

    def get_client(self, type:str, user:str='admin'):
        """ Make a client as directed by the provisioner config """
        pass
