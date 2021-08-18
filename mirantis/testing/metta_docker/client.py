"""

Metta Client plugin for a docker client using docker-py.

This class just extends the py-docker core client class, and
so it may appear quite lean while being full of features.

@see https://docker-py.readthedocs.io/en/stable/client.html

"""
import logging
import os

from docker import DockerClient

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta_health.healthcheck import Health, HealthStatus

logger = logging.getLogger("metta.contrib.docker.client.dockerpy")

METTA_PLUGIN_ID_DOCKER_CLIENT = "metta_docker_client"
""" client plugin_id for the metta dummy plugin """


# this interface is common for all Metta plugins, but CLI plugins underuse it
# Also we work around the parent constructor.
# pylint: disable=too-few-public-methods, super-init-not-called
class DockerPyClientPlugin(DockerClient):
    """Metta Client plugin for docker using the docker-py library.

    Most of the functionality is provided by the docker-py::DockerClient class,
    while the metta plugin side is respondible for configuring the client.

    """

    # This is really what it takes to configure both the plugin and the client
    # pylint: disable=too-many-arguments
    def __init__(
        self,
        environment,
        instance_id,
        host: str,
        cert_path: str,
        tls_verify: bool = True,
        compose_tls_version: str = "TLSv1_2",
        version: str = "auto",
    ):
        """Set class properties.

        In order to decorate this existing class as a DockerClient, without
        using the DockerClient constructor, nor the from_env class method, we
        have to reproduce the APIClient construction.
        We could rewrite some of the DockerClient functionality, or we can just
        create a throwaway DockerClient instance and steal its ApiClient and
        use it.

        This also lets us easily include any other env variables that might be
        in scope.

        @Note that we don't run the docker-py constructor as we build our own
            client.

        Parameters:
        -----------
        All of the arguments are handed off to the DockerClient.from_env class
        method. All arguments are converted to the related ENV equivalent if it
        had been set outside of this python code.

        host (str) [DOCKER_HOST] what daemon host to use (docker socket)

        cert_path (str) [DOCKER_CERT_PATH] path to rsa keys for authorization

        tls_verify (bool) [DOCKER_TLS_VERIFY] should the client pursue TLS
            verification

        compose_tls_version (str) [COMPOSE_TLS_VERSION] what TLS version should
            the Docker client use for docker compose.

        """
        self._environment: Environment = environment
        """ Environemnt in which this plugin exists """
        self._instance_id: str = instance_id
        """ Unique id for this plugin instance """

        logger.debug("Configuring docker client with args for host: %s", host)

        self.host = host
        self.cert_path = cert_path
        self.tls_verify = "1" if tls_verify else "0"
        self.compose_tls_version = compose_tls_version

        env = os.environ.copy()
        env["DOCKER_HOST"] = self.host
        env["DOCKER_CERT_PATH"] = self.cert_path
        env["DOCKER_TLS_VERIFY"] = self.tls_verify
        env["COMPOSE_TLS_VERSION"] = self.compose_tls_version

        # Build a client in the classical way, but we just take it's api and
        # throw the client away
        throwaway = DockerClient.from_env(environment=env, version=version)
        self.api = throwaway.api

    # deep argument is an info() standard across plugins, also we are replacing
    # the parent method.
    # pylint: disable=unused-argument, arguments-differ
    def info(self, deep: bool = False):
        """Return dict data about this plugin for introspection."""
        return {
            "docker": {
                "host": self.host,
                "cert_path": self.cert_path,
                "tls_verify": self.tls_verify,
                "compose_tls_version": self.compose_tls_version,
            }
        }

    def health(self) -> Health:
        """Determine the health of the K8s instance."""
        k8s_health = Health(source=self._instance_id, status=HealthStatus.UNKNOWN)

        for test_health_function in [self._health_swarm_nodes]:
            try:
                test_health = test_health_function()
            # pylint: disable=broad-except
            except Exception as err:
                test_health = Health(source=self._instance_id)
                test_health.critical(f"{test_health_function} exception: {err}")
            finally:
                k8s_health.merge(test_health)
        return k8s_health

    def _health_swarm_nodes(self) -> Health:
        """Check if kubernetes thinks the pod is healthy."""
        health = Health(source=self._instance_id)

        try:
            for node in self.nodes.list():
                attrs = node.attrs
                description = node.attrs["Description"]["Hostname"]
                role = node.attrs["Spec"]["Role"]

                errors: int = 0

                if "Status" in attrs:
                    node_status = node.attrs["Status"]
                    message = node_status["Message"]
                    if node_status["State"] != "ready":
                        health.error(f"Docker:Node: {role} {description} : {message}")
                        errors += 1

                if "ManagerStatus" in attrs:
                    manager_status = node.attrs["ManagerStatus"]
                    if manager_status["Reachability"] != "reachable":
                        health.error(
                            f"Docker:Node: {role} {description} : manager is not reachable"
                        )
                        errors += 1

                if node.attrs["Spec"]["Availability"] != "active":
                    health.warning(f"Docker:Node: {role} {description} : is not available")
                    errors += 1

                if errors == 0:
                    health.healthy(f"Docker:Node: {role} {description} : reports healthy")
                else:
                    health.warning(
                        f"Docker:Node: {role} {description} : is not health ({errors} issues.)"
                    )
        # pylint: disable=broad-except
        except Exception as err:
            health.error(f"Docker: could not retrieve node health: {err}")

        return health
