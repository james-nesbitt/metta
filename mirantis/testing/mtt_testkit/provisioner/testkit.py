"""
MTT Plugin: Provisioner : Plugin

"""

from mirantis.testing.tooblox.config import Config

class TestkitProvisioner:
    """
    Testkit Provisioner for MTT

    """

    def __init__(conf: Config):
        self.conf = conf

    """ Cluster Management """

    def up():
        """
        Bring up a provisioned testing cluster
        """
        pass

    def down():
        """
        Bring down a running provisioned testing cluster
        """
        pass

    """ Cluster Access """
