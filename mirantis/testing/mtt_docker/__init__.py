
import os

from mirantis.testing.mtt import plugin as mtt_plugin
from mirantis.testing.mtt.config import Config

from .plugins.client import DockerClientPlugin

MTT_PLUGIN_ID_DOCKER_CLIENT='mtt_docker'
""" client plugin_id for the mtt dummy plugin """
@mtt_plugin.Factory(type=mtt_plugin.Type.CLIENT, plugin_id=MTT_PLUGIN_ID_DOCKER_CLIENT)
def mtt_plugin_factory_client_docker(config: Config, instance_id: str = ''):
    """ create an mtt client dict plugin """
    return DockerClientPlugin(config, instance_id)
