"""

Metta docker CLI plugin.

Provides functionality to manually interact with the various docker plugins.

"""
import logging
from typing import Dict, Any

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.fixtures import Fixtures
from mirantis.testing.metta_cli.base import CliBase, cli_output

from .client import METTA_PLUGIN_ID_DOCKER_CLIENT

logger = logging.getLogger("metta.cli.docker")

METTA_PLUGIN_ID_DOCKER_CLI = "metta_docker_cli"
""" metta plugin_id for the launchpad cli plugin """

# this interface is common for all Metta plugins, but CLI plugins underuse it
# pylint: disable=too-few-public-methods
class DockerCliPlugin(CliBase):
    """Fire command/group generator for various docker plugin commands."""

    def fire(self) -> Dict[str, Any]:
        """Return command groups for Docker plugins."""
        if (
            self._environment.fixtures.get(
                plugin_id=METTA_PLUGIN_ID_DOCKER_CLIENT,
                exception_if_missing=False,
            )
            is not None
        ):

            return {"contrib": {"docker": DockerGroup(self._environment)}}

        return {}


class DockerGroup:
    """Base Fire command group for terraform client cli commands."""

    def __init__(self, environment: Environment):
        """Add additional command groups for plugins and inject environment."""
        self._environment = environment

    def _select_client(self, instance_id: str = "") -> Fixtures:
        """Pick a matching client."""
        if instance_id:
            return self._environment.fixtures.get(
                plugin_id=METTA_PLUGIN_ID_DOCKER_CLIENT,
                instance_id=instance_id,
            )

        # Get the highest priority workload
        return self._environment.fixtures.get(
            plugin_id=METTA_PLUGIN_ID_DOCKER_CLIENT,
        )

    # deep argument is an info() standard across plugins
    # pylint: disable=unused-argument
    def info(self, workload: str = "", deep: bool = False):
        """Get info about a client plugin."""
        fixture = self._select_client(instance_id=workload)
        return cli_output(fixture.info())

    # 'all' is effectively a passthrough variable
    # pylint: disable=redefined-builtin
    def container_list(self, client: str = "", all: bool = True):
        """List all containers on the docker client."""
        fixture = self._select_client(instance_id=client)
        docker = fixture.plugin

        container_info = []
        for container in docker.containers.list(all=all):
            container_info.append(
                {
                    "name": container.name,
                    "id": container.id,
                    "image": container.image.tags,
                    "status": container.status,
                }
            )

        return cli_output(container_info)

    def run_hello_world(self, client: str = ""):
        """Run the hello-world image."""
        fixture = self._select_client(instance_id=client)
        docker = fixture.plugin

        return cli_output(docker.containers.run(image="hello-world", remove=True))
