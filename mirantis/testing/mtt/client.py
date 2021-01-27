import logging
from .plugin import MTTPlugin, Type as PluginType, Factory as PluginFactory
from .config import Config

logger = logging.getLogger('mirantis.testing.mtt.client')

MTT_PLUGIN_ID_CLIENT = PluginType.CLIENT
""" Fast access to the client plugin_id """

class ClientBase(MTTPlugin):
    """ Base class for client plugins """

    def arguments(**kwargs):
        """ Receive a list of arguments for this client """
        raise NotImplemented('arguments() was not implemented for this client plugin')



def make_client(plugin_id: str, config: Config, instance_id: str = ''):
    """ Create a new client plugin

    Parameters:
    -----------

    plugin_id (str) : what client plugin should be created

    config (Config) : config object to pass to the plugin constructor
    instance_id(str) : instance_id to pass to the plugin constructor

    Returns:
    --------

    A client plugin instance

    Throws:
    -------

    Can throw a NotImplementedError if you asked for a plugin_id that has not
    been registered.

    """
    logger.debug("Creating client plugin: %s:%s".format(plugin_id, instance_id))

    try:
        client_factory = PluginFactory(MTT_PLUGIN_ID_CLIENT, plugin_id)
        client = client_factory.create(config, instance_id)

    except NotImplementedError as e:
        raise NotImplementedError("Could not create client '{}' as that plugin_id could not be found.".format(plugin_id)) from e
    except Exception as e:
        raise Exception("Could not create client '{}' as the plugin factory produced an exception".format(plugin_id)) from e


    if not isinstance(client, ClientBase):
        logger.warn("Created client plugin does not extend the clientBase")

    return client
