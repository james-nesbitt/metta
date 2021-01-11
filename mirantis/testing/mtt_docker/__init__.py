
from mirantis.testing.toolbox.config import Config
import docker
import os

def docker_client_factory(conf: Config, *passed_args, **passed_kwargs):
    """ return a new docker client plugin instance """
    env = os.environ.copy()
    env["DOCKER_HOST"] = passed_kwargs["host"]
    env["DOCKER_CERT_PATH"] = passed_kwargs["cert_path"]
    env["DOCKER_TLS_VERIFY"] = "1" if "tls_verify" in passed_kwargs and passed_kwargs["tls_verify"] else "0"
    env["COMPOSE_TLS_VERSION"] = passed_kwargs["compose_tls_version"] if "compose_tls_version" in passed_kwargs else "TLSv1_2"

    return docker.from_env(environment=env)
