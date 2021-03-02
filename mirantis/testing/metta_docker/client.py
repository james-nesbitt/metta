
from mirantis.testing.metta.client import ClientBase
from docker import DockerClient
import logging
import os

logger = logging.getLogger('metta.contrib.docker.client.dockerpy')


class DockerPyClientPlugin(ClientBase, DockerClient):
    """ metta Client plugin for docker using the docker-py library


    """

    def __init__(self, environment, instance_id, host: str, cert_path: str, tls_verify: bool = True,
                 compose_tls_version: str = 'TLSv1_2', version: str = 'auto'):
        """ Run the super constructor but also set class properties

        In order to decorate this existing class as a DockerClient, without using the
        DockerClient constructor, nor the from_env class method, we have to reproduce
        the APIClient construction.
        We could rewrite some of the DockerClient functionality, or we can just create
        a throwaway DockerClient instance and steal its ApiClient and use it.

        This also lets us easily include any other env variables that might be in
        scope.

        @Note that we don't run the docker-py constructor as we build our own client.

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
        super(ClientBase, self).__init__(environment, instance_id)

        logger.debug(
            "Configuring docker client with args for host:{}".format(host))

        self.host = host
        self.cert_path = cert_path
        self.tls_verify = '1' if tls_verify else '0'
        self.compose_tls_version = compose_tls_version

        env = os.environ.copy()
        env['DOCKER_HOST'] = self.host
        env['DOCKER_CERT_PATH'] = self.cert_path
        env['DOCKER_TLS_VERIFY'] = self.tls_verify
        env['COMPOSE_TLS_VERSION'] = self.compose_tls_version

        throwaway = DockerClient.from_env(environment=env, version=version)
        self.api = throwaway.api

    def info(self):
        """ Return dict data about this plugin for introspection """
        return {
            'docker': {
                'host': self.host,
                'cert_path': self.cert_path,
                'tls_verify': self.tls_verify,
                'compose_tls_version': self.compose_tls_version
            }
        }
