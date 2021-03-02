"""

METTA Plugin definition and management

@NOTE we would like to type hint the 'environment' variable but it would
    create a circular import. This is not totally avoidable as plugin
    holds an Environment, but an Environments creates the plugin

"""
import logging
import functools
from enum import Enum, unique

logger = logging.getLogger('metta.plugin')

METTA_PLUGIN_CONFIG_KEY_PLUGIN = 'plugin'
""" configerus .get() key for a single plugin """
METTA_PLUGIN_CONFIG_KEY_PLUGINID = 'plugin_id'
""" configerus .get() key for plugin_id """
METTA_PLUGIN_CONFIG_KEY_INSTANCEID = 'instance_id'
""" configerus .get() key for plugin_id """
METTA_PLUGIN_CONFIG_KEY_TYPE = 'type'
""" configerus .get() key for plugin type """
METTA_PLUGIN_CONFIG_KEY_ARGUMENTS = 'arguments'
""" configerus .get() key for plugin arguments """
METTA_PLUGIN_CONFIG_KEY_PRIORITY = 'priority'
""" will use this Dict key assign an instance a priority when it is created. """
METTA_PLUGIN_CONFIG_KEY_CONFIG = 'config'
""" will use this Dict key as additional config """
METTA_PLUGIN_CONFIG_KEY_VALIDATORS = 'validators'
""" will use this Dict key from the output config to decide what validators to apply to the plugin """


METTA_PLUGIN_VALIDATION_JSONSCHEMA = {
    METTA_PLUGIN_CONFIG_KEY_INSTANCEID: {'type': 'string'}
}
""" json schema validation definition for a plugin """


class METTAPlugin():
    """ Base metta Plugin which all plugins can extend """

    def __init__(self, environment: object, instance_id: str):
        """
        Parameters:
        -----------

        environment (Environment) : Environment object in which this plugin lives.

        instance_id (str) : instance id for the plugin.  A unique identifier which
            the plugin can use for naming and introspective identification.

        """
        self.environment = environment
        self.instance_id = instance_id


@unique
class Type(Enum):
    """ Enumerator to match plugin types to plugin labels """
    CLIENT = 'metta.plugin.client'
    """ Plugins which interact with clusters """
    SOURCE = 'metta.plugin.configsource'
    """ A Config source handler """
    OUTPUT = 'metta.plugin.output'
    """ A Config output handler """
    PROVISIONER = 'metta.plugin.provisioner'
    """ A cluster provisioner plugin """
    WORKLOAD = 'metta.plugin.workload'
    """ Plugins which use clients/provisioners to apply a workload to a cluster """
    CLI = 'metta.plugin.cli'
    """ Plugins extend the metta cli """

    def from_string(type_string: str) -> 'Type':
        """ Try to offer some flexibility when defining a type

        METTA Plugin enum keys are upper case keys such as "OUTPUT" or "CLIENT"
        and values are in a long form 'metta.plugin.provisioner'.  Both can be
        difficult to use, especially for config ources which can't
        programmatically access the enum.

        This function allows some flexibility in naming.

        Parameters:
        -----------

        type_string (str) : a string attempt to identify a plugin.  It can be
            an any-case form of the Type key, the full string value of a Type
            instance, or the part after 'metta.plugin.' of the value.

        Returns:
        --------

        a Type instance matching the passed string

        Raises:
        -------

        KeyError if the passed argument could not be matched.

        """
        if type is None:
            raise ValueError(
                "Cannot determine type of plugin sa you passed a None value")

        try:
            return Type(type_string)
        except ValueError:
            pass
        try:
            return Type[type_string.upper()]
        except (KeyError, AttributeError):
            pass
        try:
            return Type('metta.plugin.{}'.format(type_string))
        except ValueError:
            pass

        raise KeyError(
            "Could not identify METTA plugin type requested '{}'".format(type_string))


class Factory():
    """ Python decorator class for metta Plugin factories

    This class should be used to decorate any function which is meant to be a
    factory for metta plugins.

    If you are writing a plugin factory, decorate it with this class, provide
    the factory type and id values, and then the factory will be avaialble to
    other code.

    If you are trying to get an instance of a plugin, then create an instance of
    this class and use the create() method

    """

    registry = {}
    """ A list of all of the registered factory functions """

    def __init__(self, type: Type, plugin_id: str):
        """ register the decoration

        Parameters:
        -----------

        type (Type) : Plugin type which the factory created

        plugin_id (str) : unique identifier for the plugin which this factory
            will create.  This will be used on registration and the matching
            value is used on construction.

        """
        logger.debug(
            "Plugin factory registered `%s:%s`",
            type.value,
            plugin_id)
        self.plugin_id = plugin_id
        self.type = type

        if not self.type.value in self.registry:
            self.registry[self.type.value] = {}

    def __call__(self, func):
        """ Decorator factory wrapping function

        Returns:
        --------

        Decorated construction function(config: Config)

        """
        functools.update_wrapper(self, func)

        def wrapper(environment: object, instance_id: str, *args, **kwargs):
            logger.debug(
                "plugin factory exec: %s:%s",
                self.type.value,
                self.plugin_id)
            plugin = func(
                environment=environment,
                instance_id=instance_id,
                *args,
                **kwargs)
            if not isinstance(plugin, METTAPlugin):
                logger.warn(
                    "plugin factory did not return an instance of metta Plugin `{}:{}`".format(
                        self.type.value, self.plugin_id))

            return plugin

        self.registry[self.type.value][self.plugin_id] = wrapper
        return wrapper

    def create(self, environment: object, instance_id: str, *args, **kwargs):
        """ Get an instance of a plugin as created by the decorated

        Parameters:

        environment (Environment) : Environment object in which this plugin lives.

        instance_id (str) : instance id for the plugin.  A unique identifier which
            the plugin can use for naming and introspective identification.

        """
        try:
            factory = self.registry[self.type.value][self.plugin_id]
        except KeyError:
            raise NotImplementedError(
                "METTA Plugin instance '{}:{}' has not been registered.".format(
                    self.type.value, self.plugin_id))
        except Exception as e:
            raise Exception(
                "Could not create Plugin instance '{}:{}' as the plugin factory produced an exception".format(
                    self.type.value, self.plugin_id)) from e

        return factory(environment=environment,
                       instance_id=instance_id, *args, **kwargs)
