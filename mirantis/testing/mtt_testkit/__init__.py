
from mirantis.testing.toolbox.config import Config
from .provisioner.factory import factory

def provisioner_factory(conf: Config):
    return factory(conf)
