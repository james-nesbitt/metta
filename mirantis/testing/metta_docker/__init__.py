"""

Metta Docker.

metta contrib package for docker functionality, specifically for registering
a Docker client plugin.

"""

from typing import Any

from mirantis.testing.metta.plugin import Factory
from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.client import METTA_PLUGIN_INTERFACE_ROLE_CLIENT
from mirantis.testing.metta_health.healthcheck import METTA_PLUGIN_INTERFACE_ROLE_HEALTHCHECK
from mirantis.testing.metta.workload import METTA_PLUGIN_INTERFACE_ROLE_WORKLOAD

from mirantis.testing.metta_cli import METTA_PLUGIN_INTERFACE_ROLE_CLI

from .client import DockerPyClientPlugin, METTA_PLUGIN_ID_DOCKER_CLIENT
from .run_workload import (
    DockerPyRunWorkloadPlugin,
    METTA_PLUGIN_ID_DOCKER_RUN_WORKLOAD,
    DOCKER_RUN_WORKLOAD_CONFIG_LABEL,
    DOCKER_RUN_WORKLOAD_CONFIG_BASE,
)
from .cli import DockerCliPlugin, METTA_PLUGIN_ID_DOCKER_CLI


# This is really what it takes to configure both the metta plugin and the docker client
# pylint: disable=too-many-arguments
@Factory(
    plugin_id=METTA_PLUGIN_ID_DOCKER_CLIENT,
    interfaces=[
        METTA_PLUGIN_INTERFACE_ROLE_CLIENT,
        METTA_PLUGIN_ID_DOCKER_CLIENT,
        METTA_PLUGIN_INTERFACE_ROLE_HEALTHCHECK,
    ],
)
def metta_plugin_factory_client_dockerpy(
    environment: Environment,
    instance_id: str = "",
    host: str = "",
    cert_path: str = "",
    tls_verify: bool = True,
    compose_tls_version: str = "TLSv1_2",
    version: str = "auto",
):
    """Create an metta client for dockerpy."""
    return DockerPyClientPlugin(
        environment,
        instance_id=instance_id,
        host=host,
        cert_path=cert_path,
        tls_verify=tls_verify,
        compose_tls_version=compose_tls_version,
        version=version,
    )


@Factory(
    plugin_id=METTA_PLUGIN_ID_DOCKER_RUN_WORKLOAD,
    interfaces=[METTA_PLUGIN_INTERFACE_ROLE_WORKLOAD],
)
def metta_plugin_factory_workload_docker_run(
    environment: Environment,
    instance_id: str = "",
    label: str = DOCKER_RUN_WORKLOAD_CONFIG_LABEL,
    base: Any = DOCKER_RUN_WORKLOAD_CONFIG_BASE,
):
    """Create a docker run workload plugin."""
    return DockerPyRunWorkloadPlugin(environment, instance_id, label=label, base=base)


@Factory(plugin_id=METTA_PLUGIN_ID_DOCKER_CLI, interfaces=[METTA_PLUGIN_INTERFACE_ROLE_CLI])
def metta_docker_factory_cli(environment: Environment, instance_id: str = ""):
    """Create a docker cli plugin."""
    return DockerCliPlugin(environment, instance_id)


# ----- SetupTools EntryPoint METTA BootStrapping -----


# pylint: disable=unused-argument
def bootstrap_environment(environment: Environment):
    """METTA_Terraform bootstrap.

    Currently we only use this to import plugins.

    Parameters:
    -----------
    env (Environment) : an environment which should have validation config
        added to.

    """
