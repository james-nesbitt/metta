
import logging
from .plugin import MTTPlugin, Type as PluginType, Factory as PluginFactory
from .config import Config

logger = logging.getLogger('mirantis.testing.mtt.provisioner')

MTT_PLUGIN_ID_PROVISIONER = PluginType.PROVISIONER
""" Fast access to the Provisioner plugin_id """

class ProvisionerBase(MTTPlugin):
    "Base Provisioner plugin class"

    def apply(self):
        """ bring a cluster to the configured state """
        pass

    def destroy(self):
        """ remove all resources created for the cluster """


def make_provisioner(plugin_id: str, config: Config, instance_id: str = ''):
    """ Create a new provisioner plugin

    Parameters:
    -----------

    plugin_id (str) : what provisioner plugin should be created

    config (Config) : config object to pass to the plugin constructor
    instance_id(str) : instance_id to pass to the plugin constructor

    Returns:
    --------

    A provisioner plugin instance

    Throws:
    -------

    Can throw a NotImplementedError if you asked for a plugin_id that has not
    been registered.

    """
    logger.debug("Creating provisioner plugin: %s:%s".format(plugin_id, instance_id))
    provisioner_factory = PluginFactory(MTT_PLUGIN_ID_PROVISIONER, plugin_id)
    provisioner = provisioner_factory.create(config, instance_id)

    if not isinstance(provisioner, ProvisionerBase):
        logger.warn("Created provisioner plugin does not extend the ProvisionerBase")

    return provisioner
