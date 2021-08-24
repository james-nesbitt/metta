"""

METTA Plugin definition and management.

The basis of plugin management is here.  The functionality allows any code to
register a plugin by decorating a factory function, or to use the factory to
ask for an instance of a plugin based on type an id.

Plugins are uniquely identified using a plugin_id string.  This string is
a parte of the plugin registration, and is used when asking the Factory to
create an instance of the plugin.

Plugins also have a list of string interfaces associated during registration
which are used to allow a plugin registration to arbitrarily decide what the
plugin can do. The interfaces descriptors play no functional role, and do
not relate to any python structures, but rather is used to allow plugin
consumers to look for plugins which advertise that they do certain things.

The order of operations for using plugins should be:

1. register the plugin by decorating a function that can build the plugin
  with the Factory class.  Provide a unique id for the plugin and also
  provide any describing string interfaces.

2. optionally use some Factory class methods to discover plugin ids.

3. ask the Factory object to create a plugin instance. This returns
  whatever the decorated factory function returns, wrapper in a small
  struct container that also contains some metadata about the plugin.

"""
import logging
import functools
from typing import List, Dict, Callable, Any

logger = logging.getLogger("metta.plugin")

METTA_PLUGIN_CONFIG_KEY_PLUGIN = "plugin"
""" configerus .get() key for a single plugin """
METTA_PLUGIN_CONFIG_KEY_PLUGINID = "plugin_id"
""" configerus .get() key for plugin_id """
METTA_PLUGIN_CONFIG_KEY_INSTANCEID = "instance_id"
""" configerus .get() key for plugin_id """
METTA_PLUGIN_CONFIG_KEY_PLUGININTERFACES = "interfaces"
""" configerus .get() key for plugin interfaces """
METTA_PLUGIN_CONFIG_KEY_PLUGINLABELS = "labels"
""" configerus .get() key for plugin labels """
METTA_PLUGIN_CONFIG_KEY_ARGUMENTS = "arguments"
""" configerus .get() key for plugin arguments """


# object is a struct (better than a Dict)
# pylint: disable=too-few-public-methods, too-many-arguments
class Instance:
    """An instances of a plugin, with some metadata about it."""

    def __init__(
        self,
        plugin_id: str,
        instance_id: str,
        interfaces: List[str],
        labels: Dict[str, str],
        plugin: object,
    ):
        """Create an Instance object."""
        self.plugin_id = plugin_id
        self.instance_id = instance_id
        self.interfaces = interfaces
        self.labels = labels
        self.plugin = plugin

    def __repr__(self) -> str:
        """Create a string representation of the instance."""
        return f"Instance({self.plugin_id}, {self.instance_id}, {self.interfaces}, {self.labels})"


# object is a struct (better than a Dict)
# pylint: disable=too-few-public-methods
class PluginInstanceFactory:
    """Struct for tracking registered plugin factories with metadata."""

    def __init__(
        self,
        plugin_id: str,
        interfaces: List[str],
        labels: Dict[str, str],
        factory_method: Callable,
    ):
        """Create a new PluginFactoryStruct."""
        self.plugin_id = plugin_id
        self.interfaces = interfaces
        self.labels = labels
        self.factory_method = factory_method


class Factory:
    """Python decorator class for metta Plugin factories.

    This class should be used to decorate any function which is meant to be a
    factory for metta plugins.

    If you are writing a plugin factory, decorate it with this class, provide
    the factory type and id values, and then the factory will be avaialble to
    other code.

    If you are trying to get an instance of a plugin, then create an instance
    of this class and use the create() method

    """

    _registry: Dict[str, PluginInstanceFactory] = {}
    """ A dict of registered factory functions."""

    def __init__(
        self, plugin_id: str, interfaces: List[str] = None, labels: Dict[str, str] = None
    ):
        """Create a new Factory instance.

        This is used in two scenarios:

        1. Execution of a decoration on a factory function.
        2. Initialization of an object that will be used to for new instances.

        Parameters:
        -----------
        plugin_id (str) : unique identifier for the plugin which this factory
            will create.  This will be used on registration and the matching
            value is used on construction.

        interfaces (List[str]) : List of string identifiers for interfaces

        Raises:
        -------
        Plugin IDs must be universally unique.  Attempting to register a
        plugin with an ID that exists already will raise a KeyError
        """
        if plugin_id in self._registry:
            raise KeyError(
                f"Plugin registration failed; there is already a plugin with the name {plugin_id}"
            )

        self._plugin_id: str = plugin_id
        self._interfaces: List[str] = interfaces if interfaces is not None else []
        self._labels: Dict[str, str] = labels if labels is not None else {}

        logger.debug("Metta Plugin factory registering `%s`", self)

    def __repr__(self) -> str:
        """Reproduce string for this object."""
        return f"Factory({self._plugin_id}, {self._interfaces}, {self._labels})"

    def __call__(self, func: Callable) -> Callable:
        """Wrap the decorator factory wrapping function.

        Returns:
        --------
        Decorated construction function.

        """
        functools.update_wrapper(self, func)

        def wrapper(*args, **kwargs):
            logger.debug("plugin factory exec: %s", self._plugin_id)
            return func(*args, **kwargs)

        self._registry[self._plugin_id] = PluginInstanceFactory(
            self._plugin_id, self._interfaces, self._labels, wrapper
        )
        return wrapper

    @classmethod
    def create(
        cls,
        plugin_id: str,
        instance_id: str,
        *args: List[Any],
        **kwargs: Dict[str, Any],
    ) -> Any:
        """Get an instance of a plugin as created by the decorated factory.

        Parameters:
        -----------
        plugin_id (str) : plugin id of the plugin to be created, which must
            match a registered plugin id.

        akwargs : Arguments passed to the plugin factory as kwargs.

        @NOTE The metta environment object is the most common requestor of
            plugins, and it will always pass some arguments to every plugin
            factory, which means that plugins are expected to accept those
            arguments.
            When writing a plugin, know what arguments the factory is expected
            to handle.

        Returns:
        --------
        An instance of the plugin as created by the registered plugin factory.

        Metta core often expects this return to be an object instance of a
        plugin class, which will implemented interfaces based on the kind of
        plugin.  This is kind of abstract, but that follows the goals of the
        plugin management system, which is just hear to register and create
        plugins for coordinated functionality injection.

        """
        if not (isinstance(plugin_id, str) and isinstance(instance_id, str)):
            raise ValueError(
                f"Bad arguments passed for creating a fixture: " f":{plugin_id}:{instance_id}"
            )
        try:
            factory = cls._registry[plugin_id]
        except KeyError as err:
            raise NotImplementedError(
                f"METTA Plugin factory '{plugin_id}' has not been registered."
            ) from err
        except Exception as err:
            raise Exception(
                f"Could not create Plugin instance '{plugin_id}' due to an unknown error."
            ) from err

        plugin = factory.factory_method(*args, **kwargs)
        return Instance(
            plugin_id=plugin_id,
            instance_id=instance_id,
            interfaces=factory.interfaces,
            labels=factory.labels,
            plugin=plugin,
        )

    @classmethod
    def interfaces(cls) -> List[str]:
        """Return an iterable of types that have been registered.

        Returns:
        --------
        A list of string registered plugin ids

        """
        plugin_interfaces: List[str] = []
        for factory in cls._registry.values():
            for factory_interface in factory.interfaces:
                if factory_interface not in plugin_interfaces:
                    plugin_interfaces.append(factory_interface)
        return plugin_interfaces

    @classmethod
    def plugin_ids(cls, interfaces_filter: List[str] = None) -> List[str]:
        """Build a generator of matching registered plugins.

        Parameters:
        -----------
        interfaces_filter (List[str]) : if not empty, then only plugins which
            have all of the passed interfaces are included in the return.

        Returns:
        --------
        A List of plugin ids for all matching plugins (which is all plugins
        if you passed an empty filter list)
        """
        if interfaces_filter is None:
            interfaces_filter = []

        if len(interfaces_filter) == 0:
            return list(cls._registry.keys())

        plugin_ids: List[str] = []
        for factory in cls._registry.values():
            for interface_filter in interfaces_filter:
                if interface_filter not in factory.interfaces:
                    break
            else:
                # interfaces do intersect
                plugin_ids.append(factory.plugin_id)

        return plugin_ids
