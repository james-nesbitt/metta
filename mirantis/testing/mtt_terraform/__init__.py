
from mirantis.testing.toolbox.config import Config
from .provisioner import TerraformProvisioner

def provisioner_factory(conf: Config):
    """ MTT plugin load entry_point for the provisioner plugin """
    return TerraformProvisioner(conf)
