
from mirantis.testing.toolbox.config import Config
from .provisioner import LaunchpadProvisioner
from .client import LaunchpadExecClient

def provisioner_factory(conf: Config):
    """ create an mtt provisioner plugin for launchpad """
    return LaunchpadProvisioner(conf)

def exec_client_factory(conf: Config):
    """ A client that can exec on hosts in a launchpad cluster """
    return LaunchpadExecClient(conf)
