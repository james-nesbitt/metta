"""

metta Docker

metta contrib package for docker functionality, specifically for registering
a Docker client plugin.

"""

from typing import Any

from mirantis.testing.metta.plugin import Factory, Type
from mirantis.testing.metta.environment import Environment

from .client import DockerPyClientPlugin
from .run_workload import DockerPyRunWorkloadPlugin, DOCKER_RUN_WORKLOAD_CONFIG_LABEL, DOCKER_RUN_WORKLOAD_CONFIG_BASE

METTA_PLUGIN_ID_DOCKER_CLIENT = 'metta_docker'
""" client plugin_id for the metta dummy plugin """


@Factory(type=Type.CLIENT, plugin_id=METTA_PLUGIN_ID_DOCKER_CLIENT)
def metta_plugin_factory_client_dockerpy(
    environment: Environment, instance_id: str = '', host: str = '', cert_path: str = '', tls_verify: bool = True,
        compose_tls_version: str = 'TLSv1_2', version: str = 'auto'):
    """ create an metta client for dockerpy """
    return DockerPyClientPlugin(environment, instance_id=instance_id,
                                host=host, cert_path=cert_path, tls_verify=tls_verify, compose_tls_version=compose_tls_version, version=version)


METTA_PLUGIN_ID_DOCKER_RUN_WORKLOAD = 'metta_docker_run'
""" workload plugin_id for the docker run plugin """


@Factory(type=Type.WORKLOAD, plugin_id=METTA_PLUGIN_ID_DOCKER_RUN_WORKLOAD)
def metta_plugin_factory_workload_docker_run(
        environment: Environment, instance_id: str = '', label: str = DOCKER_RUN_WORKLOAD_CONFIG_LABEL, base: Any = DOCKER_RUN_WORKLOAD_CONFIG_BASE):
    """ create a docker run workload plugin """
    return DockerPyRunWorkloadPlugin(
        environment, instance_id, label=label, base=base)


""" SetupTools EntryPoint METTA BootStrapping """


def bootstrap(environment: Environment):
    """ METTA_Docker bootstrap

    We dont't take any action.  Our purpose is to run the above factory
    decorators to register our plugins.

    """
    pass
