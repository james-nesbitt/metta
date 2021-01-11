"""

A mock provisioner to act as a backend when the cluster is already provisioned

"""

import yaml
import logging
import os.path

logger = logging.getLogger("mirantis.testing.mtt_launchpad.existing")

class ExistingBackendProvisioner:
    """ Existing backend provisioner """

    def __init__(self, output_name: str, config_file: str):
        """

        output_name (str) : which output name should return the laucnhpad config
        config_file (str) : path to the file to use for launchpad config

        """
        self.output_name = output_name
        self.config_file = config_file
        self.working_dir = os.path.dirname(self.config_file)

    """ MOCK cluster management """

    def prepare(self):
        pass

    def up(self):
        pass

    def down(self):
        pass

    def output(self, name: str):
        """ Return our mock output name """

        if name == self.output_name:
            try:
                with open(self.config_file, 'r') as config_file:
                    return config_file.read()
            except FileNotFoundError as e:
                raise ValueError("Existing launchpad file could not be found: %s", self.config_file)
