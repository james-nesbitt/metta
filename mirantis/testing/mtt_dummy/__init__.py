
from mirantis.testing.toolbox.config import Config
from .client import DummyClient
from .provisioner import DummyProvisioner
from .workload import DummyWorkload

def client_factory(conf: Config):
    """ return a new mtt_dummy client plugin instance """
    return DummyClient(conf)

def provisioner_factory(conf: Config):
    """ return a new mtt_dummy provisioner plugin instance """
    return DummyProvisioner(conf)

def workload_factory(conf: Config):
    """ return a new mtt_dummy workload plugin instance """
    return DummyWorkload(conf)
