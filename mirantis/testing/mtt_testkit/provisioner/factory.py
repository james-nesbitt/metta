"""
MTT Plugin Factory for testkit provisioner plugins

"""

from mirantis.testing.toolbox.config import Config
from .testkit import TestkitProvisioner

def factory(conf: Config):
    """
    Implement the interface for mtt:plugin_load, returning a testkit provisioner
    plugin object

    """
    return TestkitProvisioner(conf)
