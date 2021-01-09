"""

Plugin related functionality

A plugin is an injected object that can be defined in any python package/distr
that matches some expected behaviour.  The behaviours is not enforced but rather
duck-typed.
Some interfaces are defined below to give engineers an idea on how it works.

Why: because external injection allows anyone to use the toolbox without being
    limited to our lower level functionality.

How:

Any python package can declare in a setuptools entrypoint for the plugin type
(string as found in the enum) a plugin factory (function) which will receive
a Config object and return the plugin object.
Plugins don't have access to anything other than the Config, but that is pretty
flexible.
Plugins can consume/wrap other plugins, but they can create their own toolbox
instances with the shared config and use the toolbox methods to create more
plugin instances.

"""

import logging
from .config import Config
from enum import Enum, unique
from importlib import metadata

logger = logging.getLogger("mirantis.testing.toolbox.plugin")

@unique
class PluginType(Enum):
    """ Enumerator to match plugin types to plugin labels

    We enforce that we only load plugins of known types through this enumerator
    which is perhaps a flexibility weakness without any real advantage.

    """

    CLIENT      = "mirantis.testing.toolbox.plugin.client"
    """ Plugins which interact with clusters """
    PROVISIONER = "mirantis.testing.toolbox.plugin.provisioner"
    """ A cluster provisioner plugin """
    WORKLOAD    = "mirantis.testing.toolbox.plugin.workload"
    """ Plugins which use clients/provisioners to apply a workload to a cluster """

def load_plugin(conf: Config, type: PluginType, name: str, *passed_args, **passed_kwargs):
    """
    Make a plugin object instance of a type and key

    A python module out there will need to have declared an entry_point for
    'mirantis.testing.toolbox.{type}' with entry_point key {name}.
    The entrypoint must be a factory method of signature:
    ```
        def XXXX(conf: mirantis.testing.toolbox.config.Config) -> {plugin}:
    ```

    The factory should return the plugin, which is likely going to be some kind
    of an object which has value to the caller of the function. This function
    does not specify what the return needs to be.
    """
    logger.info("Loading plugin %s.%s", type.value, name)
    eps = metadata.entry_points()[type.value]
    for ep in eps:
        if ep.name == name:
            plugin = ep.load()
            return plugin(conf, *passed_args, **passed_kwargs)
    else:
        logger.error("Plugin loader could not find the requested plugin '%s' of type '%s'.  Valid types are %s", type.value, name, eps)
        raise KeyError("Plugin not found {}.{}".format(type.value, name))


""" INTERFACES (for patterning only, non-functional) """


def PluginFactoryInterface(conf: Config):
    """

    Interface for the plugin entry_point, which is expected to be a plugin
    factory, which uses a Config loader and created a plugin instance

    Arguments
    ---------

    conf Config:
        a config object that can be used to load config for operation

        @TODO should this be a Loaded Config object based on loading
            "provisioner" or perhaps on the plugin name

    Returns:
    --------

    An object that implements the expected behaviour for the plugin type

    """
    pass

class PluginInterface:
    """
    An Attempt at an interface for all plugin classes.

    This is never actually enforced, but is meant as a guideline.
    """

    def __init__(conf: Config, *passed_args, **passed_kwargs):
        """

        Create a new instance of the provisioner.

        Arguments
        ---------

        conf Config:
            a config object that can be used to load config for operation

            @TODO should this be a Loaded Config object based on loading
                "provisioner" or perhaps on the plugin name

        Any other arguments that you want as passed in by the load_plugin
        call.
        """
        pass


class ProvisionerInterface(PluginInterface):
    """

    Plugins that manage testing clusters

    """

    """ Cluster Management """

    def prepare(self):
        """

        Prepare the provisioner for starting a testing cluster.

        """

    def up(self):
        """

        Bring up a cluster based on the configuration

        """
        pass

    def down(self):
        """

        Bring down any running cluster

        """
        pass

    def info(self):
        """

        Provide a Dict of information about the cluster configuration

        Returns:

        """


    """ Cluster Interaction """
