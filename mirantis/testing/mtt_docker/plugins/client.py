
import logging
import os

logger = logging.getLogger("mirantis.testing.mtt_docker.client")

from docker import DockerClient

from mirantis.testing.mtt.client import ClientBase

class DockerClientPlugin(ClientBase, DockerClient):
    """ MTT Client plugin for docker

    We need to have the ClientBase constructor called, not the DockerClient one

    """

    def args(self, host:str, cert_path:str, tls_verify:bool=True, compose_tls_version:str='TLSv1_2'):
        """ Build the DockerClient

        In order to decorate this existing class as a DockerClient, without using the
        DockerClient constructor, nor the from_env class method, we have to reproduce
        the APIClient construction.
        We could rewrite some of the DockerClient functionality, or we can just create
        a throwaway DockerClient instance and steal its ApiClient and use it.

        This also lets us easily include any other env variables that might be in
        scope.

        Parameters:
        -----------

        All of the arguments are handed off to the DockerClient.from_env class method.
        All arguments are converted to the related ENV equivalent if it had been set
        outside of this python code.

        host (str) [DOCKER_HOST] what daemon host to use (docker socket)
        cert_path (str) [DOCKER_CERT_PATH] path to rsa keys for authorization
        tls_verify (bool) [DOCKER_TLS_VERIFY] should the client pursue TLS verification
        compose_tls_version (str) [COMPOSE_TLS_VERSION] what TLS version should
            the Docker client use for docker compose.

        """
        logger.debug("Configuring docker client with args for host:{}".format(host))

        env = os.environ.copy()
        env["DOCKER_HOST"] = host
        env["DOCKER_CERT_PATH"] = cert_path
        env["DOCKER_TLS_VERIFY"] = "1" if tls_verify else "0"
        env["COMPOSE_TLS_VERSION"] = compose_tls_version

        throwaway = DockerClient.from_env(environment=env)
        self.api = throwaway.api
