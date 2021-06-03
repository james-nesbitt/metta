"""

METTA Plugin definition and management.

The basis of plugin management is here.  The functionality allows any code to
register a plugin by decorating a factory function, or to use the factory to
ask for an instance of a plugin based on type an id.

Plugins have two important pieces of metadata for their type:

1. Plugin_type : an arbitrary string label which allows semantic grouping of
        plugins.  Type is used for loose retrieval, for example "to get all of
        the CLI plugin types", but is also used for introspection (checking
        out what we have.)
2. Plugin_Id : an arbitrary string used to label the specific plugin type.
        This means that when trying to get an instance of a specific plugin,
        this value can be used.

"""
import logging
import functools
from typing import Dict, Callable

logger = logging.getLogger('metta.plugin')

METTA_PLUGIN_CONFIG_KEY_PLUGIN = 'plugin'
""" configerus .get() key for a single plugin """
METTA_PLUGIN_CONFIG_KEY_PLUGINID = 'plugin_id'
""" configerus .get() key for plugin_id """
METTA_PLUGIN_CONFIG_KEY_INSTANCEID = 'instance_id'
""" configerus .get() key for plugin_id """
METTA_PLUGIN_CONFIG_KEY_PLUGINTYPE = 'plugin_type'
""" configerus .get() key for plugin type """
METTA_PLUGIN_CONFIG_KEY_ARGUMENTS = 'arguments'
""" configerus .get() key for plugin arguments """
METTA_PLUGIN_CONFIG_KEY_PRIORITY = 'priority'
""" configerus .get()  assign an instance a priority when it is created. """
METTA_PLUGIN_CONFIG_KEY_CONFIG = 'config'
""" configerus .get()  as additional config """
METTA_PLUGIN_CONFIG_KEY_VALIDATORS = 'validators'
""" configerus .get()  to decide what validators to apply to the plugin """


METTA_PLUGIN_VALIDATION_JSONSCHEMA = {
    METTA_PLUGIN_CONFIG_KEY_INSTANCEID: {'plugin_type': 'string'}
}
""" json schema validation definition for a plugin """


class Factory():
    """Python decorator class for metta Plugin factories.

    This class should be used to decorate any function which is meant to be a
    factory for metta plugins.

    If you are writing a plugin factory, decorate it with this class, provide
    the factory type and id values, and then the factory will be avaialble to
    other code.

    If you are trying to get an instance of a plugin, then create an instance
    of this class and use the create() method

    """

    registry: Dict[str, Dict[str, Callable]] = {}
    """ A dict of registered factory functions, grouped by plugin type """

    def __init__(self, plugin_type: str, plugin_id: str):
        """Create a new Factory instance.

        This is used in two scenarios:

        1. Execution of a decoration on a factory function.
        2. Initialization of an object that will be used to for new instances.

        Parameters:
        -----------
        plugin_type (str) : Plugin type label which the factory created
            pylint W0622 this is used only in this function and it makes for a
            much more natural decorator syntax

        plugin_id (str) : unique identifier for the plugin which this factory
            will create.  This will be used on registration and the matching
            value is used on construction.

        """
        logger.debug("Metta Plugin factory registering `%s:%s`", plugin_type, plugin_id)
        self.plugin_id: str = plugin_id
        self.plugin_type: str = plugin_type

        if self.plugin_type not in self.registry:
            self.registry[self.plugin_type] = {}

    def __call__(self, func: Callable):
        """Wrap the decorator factory wrapping function.

        Returns:
        --------
        Decorated construction function.

        """
        functools.update_wrapper(self, func)

        def wrapper(environment: object, instance_id: str, *args, **kwargs):
            logger.debug("plugin factory exec: %s:%s", self.plugin_type, self.plugin_id)
            plugin = func(
                environment=environment,
                instance_id=instance_id,
                *args,
                **kwargs)

            return plugin

        self.registry[self.plugin_type][self.plugin_id] = wrapper
        return wrapper

    def create(self, environment: object, instance_id: str, *args, **kwargs) -> object:
        """Get an instance of a plugin as created by the decorated.

        Parameters:
        -----------
        environment (Environment) : Environment object in which this plugin
            lives.

        instance_id (str) : instance id for the plugin.  A unique identifier
            which the plugin can use for naming and introspective
            identification.

        """
        try:
            factory = self.registry[self.plugin_type][self.plugin_id]
        except KeyError as err:
            raise NotImplementedError(
                f"METTA Plugin instance '{self.plugin_type}:{self.plugin_id}' "
                "has not been registered.") from err
        except Exception as err:
            raise Exception(
                f"Could not create Plugin instance '{self.plugin_type}:{self.plugin_id}' "
                "due to an unknown error.") from err

        return factory(environment=environment,
                       instance_id=instance_id, *args, **kwargs)

    @classmethod
    def plugin_types(cls):
        """Return a generator of types that have been registered."""
        return cls.registry.keys()

    @classmethod
    def plugins(cls, plugin_type: str):
        """Return a generator of registered plugin keys for a passed plugin type registered."""
        return cls.registry[plugin_type].keys()
