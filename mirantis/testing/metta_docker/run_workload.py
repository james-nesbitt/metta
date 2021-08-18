"""

Docker workload plugin to run docker run commands, given docker host config.

This type of docker workload is simple to use but perhaps not
very feature rich.

"""
from typing import Any
import logging

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.fixture import Fixtures

from .client import DockerPyClientPlugin, METTA_PLUGIN_ID_DOCKER_CLIENT

logger = logging.getLogger("metta_docker.workload.run")

METTA_PLUGIN_ID_DOCKER_RUN_WORKLOAD = "metta_docker_run_workload"
""" metta plugin_id for the launchpad cli plugin """

DOCKER_RUN_WORKLOAD_CONFIG_LABEL = "docker"
""" Configerus label for retrieving docker run workloads """
DOCKER_RUN_WORKLOAD_CONFIG_BASE = "workload.run"
""" Configerus get base for retrieving the default run workload """

DOCKER_RUN_WORKLOAD_CONFIG_KEY_RUN = "run"
""" Configerus get base for the docker run arguments e.g. image: """


class DockerPyRunWorkloadPlugin:
    """Docker Run workload class for the DockerPy."""

    def __init__(
        self,
        environment: Environment,
        instance_id: str,
        label: str = DOCKER_RUN_WORKLOAD_CONFIG_LABEL,
        base: Any = DOCKER_RUN_WORKLOAD_CONFIG_BASE,
    ):
        """Run the super constructor but also set class properties.

        Parameters:
        -----------
        outputs (Dict[Dict]) : pass in a dictionary which defines outputs that
            should be returned

        clients (Dict[Dict]) : pass in a dictionary which defines which clients
            should be requested when working on a provisioner

        """
        self._environment: Environment = environment
        """ Environemnt in which this plugin exists """
        self._instance_id: str = instance_id
        """ Unique id for this plugin instance """

        self._config_label = label
        """ configerus load label that should contain all of the config """
        self._config_base = base
        """ configerus get key that should contain all tf config """

        run_config = self._environment.config().load(self._config_label)
        """Configerus LoadedConfig for the docker run label."""

        self._run_settings = run_config.get(
            [self._config_base, DOCKER_RUN_WORKLOAD_CONFIG_KEY_RUN]
        )
        """Arguments for docker run."""

        self._docker_client: DockerPyClientPlugin = None
        """Metta Docker client plugin."""

        # do an initial prepare in case it is never properly run
        try:
            self.prepare()
        # pylint: disable=broad-except
        except Exception:
            pass

    # deep argument is an info() standard across plugins
    # pylint: disable=unused-argument
    def info(self, deep: bool = False):
        """Return dict data about this plugin for introspection."""
        return {
            "workload": {
                "run": self._run_settings,
                "required_fixtures": {
                    "docker": {
                        "plugin_id": [METTA_PLUGIN_ID_DOCKER_CLIENT],
                    }
                },
            }
        }

    def prepare(self, fixtures: Fixtures = None):
        """Create a workload instance from a set of fixtures.

        Parameters:
        -----------
        fixtures (Fixtures) : a set of fixtures that this workload will use to
            retrieve a docker client plugin.

        """
        if fixtures is None:
            fixtures = self._environment.fixtures()

        self._docker_client = fixtures.get_plugin(interfaces=[METTA_PLUGIN_ID_DOCKER_CLIENT])

    def apply(self):
        """Run the workload.

        @NOTE Needs a docker client fixture to run.  Use .set_fixtures() first

        """
        assert "image" in self._run_settings, "Run command had no image"

        return self._docker_client.containers.run(**self._run_settings)

    # pylint: disable=fixme, no-self-use
    # TODO write the docker container rm
    def destroy(self):
        """Destroy a created docker run."""
        logger.warning("docker run workload destroy functionality is @TODO.")
