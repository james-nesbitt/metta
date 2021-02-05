"""

MTT Docker

MTT contrib package for docker functionality, specifically for registering
a Docker client plugin.

"""

import os
from configerus.config import Config

from mirantis.testing.mtt import plugin as mtt_plugin

from .plugins.client import DockerClientPlugin

MTT_PLUGIN_ID_DOCKER_CLIENT='mtt_docker'
""" client plugin_id for the mtt dummy plugin """
@mtt_plugin.Factory(type=mtt_plugin.Type.CLIENT, plugin_id=MTT_PLUGIN_ID_DOCKER_CLIENT)
def mtt_plugin_factory_client_docker(config: Config, instance_id: str = ''):
    """ create an mtt client dict plugin """
    return DockerClientPlugin(config, instance_id)


def configerus_bootstrap(config:Config):
    """ MTT_Docker configerus bootstrap

    We dont't take any action.  Our purpose is to run the above factory
    decorators to register our plugins.

    """
    pass
