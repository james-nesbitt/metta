"""

Docker client plugin

"""

from typing import List
import logging
import docker

logger = logging.getLogger("mirantis.testing.mtt_docker.client")

def factory(conf):
    """ Docker client plugin factory (see mtt/plugin/factory) """
    return DockerClient(conf)

class DockerClient(ocker):
    """ Docker client class """

    def __init__(self, conf, host, cert_path):
        """ constructor """
        self.conf = conf
        """Config object """
        self.provisioner = None
        """Provisioner object"""

        self.host = host
        self.cert_path = cert_path
        self.tls_verify=True
        self.compose_tls_version="TLSv1_2"

        self.docker_bin = "docker"

        # @TODOD should we try to load docker config ?

    def _client_from_eng

    def set_provisioner(prov):
        """ assign a provisioner object """
        self.provisioner = prov

    def assign_docker_vars(self, host: str, cert_path: str):
        """ get all docker configuration in place to execute """
        self.host = host
        self.cert_path = cert_path

        env = os.environ
        env["DOCKER_HOST"] = self.host
        env["DOCKER_CERT_PATH"] = self.cert_path
        env["DOCKER_TLS_VERIFY"] = "1" if self.tls_verify else "0"
        env["COMPOSE_TLS_VERSION"] = self.compose_tls_version
