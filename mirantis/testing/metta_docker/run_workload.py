"""

Docker workload plugin to run docker run commands, given docker host config.

This type of docker workload is simple to use but perhaps not
very feature rich.

"""
from typing import Any
import logging

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.fixtures import Fixtures
from mirantis.testing.metta.client import METTA_PLUGIN_TYPE_CLIENT
from mirantis.testing.metta.workload import WorkloadBase, WorkloadInstanceBase

logger = logging.getLogger('metta.contrib.docker.workload.run')

DOCKER_RUN_WORKLOAD_CONFIG_LABEL = 'docker'
""" Configerus label for retrieving docker run workloads """
DOCKER_RUN_WORKLOAD_CONFIG_BASE = 'workload.run'
""" Configerus get base for retrieving the default run workload """


class DockerPyRunWorkloadPlugin(WorkloadBase):
    """Docker Run workload class for the DockerPy."""

    def __init__(
            self,
            environment: Environment,
            instance_id: str,
            label: str = DOCKER_RUN_WORKLOAD_CONFIG_LABEL,
            base: Any = DOCKER_RUN_WORKLOAD_CONFIG_BASE):
        """Run the super constructor but also set class properties.

        Parameters:
        -----------
        outputs (Dict[Dict]) : pass in a dictionary which defines outputs that
            should be returned

        clients (Dict[Dict]) : pass in a dictionary which defines which clients
            should be requested when working on a provisioner

        """
        self.environment = environment
        """ Environemnt in which this plugin exists """
        self.instance_id = instance_id
        """ Unique id for this plugin instance """

        logger.info("Preparing Docker run setting")

        self.config_label = label
        """ configerus load label that should contain all of the config """
        self.config_base = base
        """ configerus get key that should contain all tf config """

    def create_instance(self, fixtures: Fixtures):
        """Create a workload instance from a set of fixtures.

        Parameters:
        -----------
        fixtures (Fixtures) : a set of fixtures that this workload will use to
            retrieve a docker client plugin.

        """
        client = fixtures.get_plugin(
            plugin_type=METTA_PLUGIN_TYPE_CLIENT, plugin_id='metta_docker')

        run_config = self.environment.config.load(self.config_label)
        """ get a configerus LoadedConfig for the docker run label """

        run = run_config.get([self.config_base, 'run'])

        return DockerRunWorkloadInstance(client, run)

    def info(self):
        """Return dict data about this plugin for introspection."""
        run_config = self.environment.config.load(self.config_label)
        """ get a configerus LoadedConfig for the docker run label """

        return {
            'workload': {
                'run': {
                    'run': run_config.get([self.config_base, 'run'])
                },
                'required_fixtures': {
                    'docker': {
                        'plugin_type': METTA_PLUGIN_TYPE_CLIENT,
                        'plugin_id': 'metta_docker'
                    }
                }
            }
        }


# This is a small workload instance, but it does its job
# pylint: disable=too-few-public-methods
class DockerRunWorkloadInstance(WorkloadInstanceBase):
    """ A workload instance for a docker run """

    def __init__(self, client, run):
        """Inject docker client, and run definition into workload instance."""
        self.client = client
        self.run = run

    def apply(self):
        """Run the workload.

        @NOTE Needs a docker client fixture to run.  Use .set_fixtures() first

        """
        assert 'image' in self.run, "Run command had no image"

        self.run = self.client.containers.run(**self.run)
        return self.run

    # @TODO write the docker container rm
    def destroy(self):
        """Destroy a created docker run."""
