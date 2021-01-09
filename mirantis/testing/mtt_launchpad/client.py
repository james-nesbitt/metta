"""

Launchpad client plugin

This plugin handles

1. shell type exec

"""

from typing import List, Dict

class LaunchpadExecClient:
    """ Launchpad client class

    this is an exec style client, which can 'run commands' on hosts

    """

    def __init__(self, conf):
        """ constructor """
        self.conf = conf
        self.provisioner = None

    def set_provisioner(prov):
        """ Assign a launchpad provisioner for backend execution """
        self.provisioner = prov

    def exec(self, cmd: List[str], env: Dict[str,str]):
        """ Run a shell command """
        pass
