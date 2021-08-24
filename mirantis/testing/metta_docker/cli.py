"""

Metta docker CLI plugin.

Provides functionality to manually interact with the various docker plugins.

"""
import logging
from typing import Dict, Any

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.fixture import Fixtures
from mirantis.testing.metta_health.healthcheck import Health
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
            self._environment.fixtures().get(
                plugin_id=METTA_PLUGIN_ID_DOCKER_CLIENT,
                exception_if_missing=False,
            )
            is not None
        ):

            return {"docker": DockerClientGroup(self._environment)}

        return {}


class DockerClientGroup:
    """Base Fire command group for terraform client cli commands."""

    def __init__(self, environment: Environment):
        """Add additional command groups for plugins and inject environment."""
        self._environment: Environment = environment

    def _select_client(self, instance_id: str = "") -> Fixtures:
        """Pick a matching client."""
        if instance_id:
            return self._environment.fixtures().get(
                plugin_id=METTA_PLUGIN_ID_DOCKER_CLIENT,
                instance_id=instance_id,
            )

        # Get the highest priority workload
        return self._environment.fixtures().get(
            plugin_id=METTA_PLUGIN_ID_DOCKER_CLIENT,
        )

    # deep argument is an info() standard across plugins
    # pylint: disable=unused-argument
    def info(self, workload: str = "", deep: bool = False):
        """Get info about a client plugin."""
        docker_fixture = self._select_client(instance_id=workload)
        return cli_output(docker_fixture.info())

    def health(self, client: str = ""):
        """Run healthcheck."""
        fixture = self._select_client(instance_id=client)
        plugin = fixture.plugin
        health: Health = plugin.health()
        return cli_output(
            {
                "fixture": {
                    "plugin_id": fixture.plugin_id,
                    "instance_id": fixture.instance_id,
                    "priority": fixture.priority,
                },
                "status": health.status(),
                "messages": list(health.messages()),
            }
        )

    def swarm_info(self, client: str = ""):
        """List all containers on the docker client."""
        docker_client = self._select_client(instance_id=client).plugin
        return cli_output(
            {
                "version": docker_client.swarm.version,
                "attrs": docker_client.swarm.attrs,
            }
        )

    def nodes_list(self, client: str = ""):
        """List all nodes in the docker swarm."""
        docker_client = self._select_client(instance_id=client).plugin
        return cli_output(
            list(
                {
                    "id": node.id,
                    "short_id": node.short_id,
                    "version": node.version,
                    "attrs": node.attrs,
                }
                for node in docker_client.nodes.list()
            )
        )

    # 'all' is effectively a passthrough variable
    # pylint: disable=redefined-builtin
    def container_list(self, client: str = "", all: bool = True):
        """List all containers on the docker client."""
        docker_client = self._select_client(instance_id=client).plugin
        container_info = []
        for container in docker_client.containers.list(all=all):
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
        docker_client = self._select_client(instance_id=client).plugin
        return cli_output(docker_client.containers.run(image="hello-world", remove=True))
