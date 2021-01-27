
import logging
from .plugin import MTTPlugin, Type as PluginType, Factory as PluginFactory
from .config import Config

logger = logging.getLogger('mirantis.testing.mtt.provisioner')

MTT_PLUGIN_ID_PROVISIONER = PluginType.PROVISIONER
""" Fast access to the Provisioner plugin_id """

class ProvisionerBase(MTTPlugin):
    "Base Provisioner plugin class"

    def prepare(self):
        """ Prepare the provisioner to apply resources """
        pass

    def apply(self):
        """ bring a cluster to the configured state """
        pass

    def destroy(self):
        """ remove all resources created for the cluster """
        pass

    def get_output(self, name:str):
        """ retrieve an output from the provisioner """
        pass

    def get_client(self, type:str, index:str=''):
        """ make a client of the type, and optionally of the index """
        pass


def make_provisioner(plugin_id:str, config:Config, instance_id:str=''):
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

    if not plugin_id:
        raise KeyError("Could not create a provisioner as an invalid plugin_id was given: '{}'".format(plugin_id))
    try:
        provisioner_factory = PluginFactory(MTT_PLUGIN_ID_PROVISIONER, plugin_id)
        provisioner = provisioner_factory.create(config, instance_id)

    except NotImplementedError as e:
        raise NotImplementedError("Could not create provisioner '{}' as that plugin_id could not be found.".format(plugin_id)) from e


    if not isinstance(provisioner, ProvisionerBase):
        logger.warn("Created provisioner plugin does not extend the ProvisionerBase")

    return provisioner
