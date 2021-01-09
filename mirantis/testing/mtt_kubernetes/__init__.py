
from mirantis.testing.toolbox.config import Config
from .client import KubernetesClient
from .workload import KubernetesApplyWorkload

def kubernetes_client_factory(conf: Config, *passed_args, **passed_kwargs):
    """ return a new kubernetes api_client """
    config_file = passed_kwargs["config_file"]
    context = passed_kwargs["config_file"] if "config_file" in passed_kwargs else None
    return client.KubernetesClient(conf, config_file=config_file, context=context)

def apply_workload_factory(conf: Config):
    """ return a new kubernetes workload plugin instance """
    return KubernetesApplyWorkload(conf)
