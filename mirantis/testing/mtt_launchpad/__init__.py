
import subprocess
from mirantis.testing.toolbox.config import Config
from .provisioner import LaunchpadProvisioner
from .client import LaunchpadExecClient

def mtt_launchpad_bootstrap(config):
    """ bootstrap the passed toolbox config for mtt lauchpad functionality """
    try:
        subprocess.run(["which", "launchpad"])
    except:
        raise Exception("The Launchpad package was unable to find the launchpad binary.  " \
            "Launchpad must be installed before this plugin can be used")

def provisioner_factory(conf: Config):
    """ create an mtt provisioner plugin for launchpad """
    return LaunchpadProvisioner(conf)

def exec_client_factory(conf: Config):
    """ A client that can exec on hosts in a launchpad cluster """
    return LaunchpadExecClient(conf)
