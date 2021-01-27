
import functools
import logging
from enum import Enum, unique

logger = logging.getLogger('mirantis.testing.mtt.plugin')

class MTTPlugin():
    """ Base MTT Plugin which all plugins can extend """

    def __init__(self, config, instance_id: str):
        """
        Parameters:
        -----------

        config (Config) : all plugins receive a config object

        id (str) : instance id for the plugin.

        """
        self.config = config
        self.instance_id = instance_id

@unique
class Type(Enum):
    """ Enumerator to match plugin types to plugin labels """
    CLIENT        = "mirantis.testing.toolbox.plugin.client"
    """ Plugins which interact with clusters """
    CONFIGSOURCE  = "mirantis.testing.toolbox.plugin.configsource"
    """ A Config source handler """
    PROVISIONER   = "mirantis.testing.toolbox.plugin.provisioner"
    """ A cluster provisioner plugin """
    WORKLOAD      = "mirantis.testing.toolbox.plugin.workload"
    """ Plugins which use clients/provisioners to apply a workload to a cluster """

class Factory():
    """ Python decorator class for MTT Plugin factories

    This class should be used to decorate any function which is meant to be a
    factory for MTT plugins.

    If you are writing a plugin factory, decorate it with this class, provide
    the factory type and id values, and then the factory will be avaialble to
    other code.

    If you are trying to get an instance of a plugin, then create an instance of
    this class and use the create() method

    """

    registry = {}
    """ A list of all of the registered factory functions """

    def __init__(self, type: Type, plugin_id: str):
        """ register the decoration """
        logger.debug("Plugin factory registered `%s:%s`", type.value, plugin_id)
        self.plugin_id = plugin_id
        self.type = type

        if not self.type.value in self.registry:
            self.registry[self.type.value] = {}

    def __call__(self, func):
        """ call the decorated function

        Returns:

        wrapped function(config: Config)
        """
        def wrapper(config, instance_id: str):
            logger.debug("plugin factory exec: %s:%s", self.type.value, self.plugin_id)
            plugin = func(config=config, instance_id=instance_id)
            if not isinstance(plugin, MTTPlugin):
                logger.warn("plugin factory did not return an instance of MTT Plugin `{}:{}`".format(self.type.value, self.plugin_id))

            return plugin

        self.registry[self.type.value][self.plugin_id] = wrapper
        return wrapper

    def create(self, config, instance_id: str):
        """ Get an instance of a plugin as created by the decorated """
        try:
            factory = self.registry[self.type.value][self.plugin_id]
        except KeyError:
            raise NotImplementedError("MTT Plugin instance '{}:{}' has not been registered.".format(self.type.value, self.plugin_id))
        except Exception as e:
            raise Exception("Could not create Plugin instance '{}:{}' as the plugin factory produced an exception".format(self.type.value, self.plugin_id)) from e

        return factory(config=config, instance_id=instance_id)
