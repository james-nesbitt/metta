"""

The MTT toolbox class and factory function

"""

import logging
from .config import Config
from .plugin import PluginType, load_plugin

MTT_PACKAGE_BOOTSTRAP_ENTRYPOINT = "mirantis.testing.toolbox.bootstrap"
""" setuptools entrypoint for boostrapping a module """

logger = logging.getLogger("mirantis.testing.toolbox")

class Toolbox:
    """

The MTT toolbox

A centralized single object which can act as a single access point to the other
tools in mtt.
The primary advantage of a single object is that it can pass info between parts
of the toolbox on its own without the consumer needing to keep track, or even
be aware of the parts.

The toolbox is heaily configuration based.  For example, the provisioner request
is served by first using configuration in a predictable way to determine which
plugin is to be used.

A aingle access object is not very "python"ish but it does allow for:
1. a central fixture for simple importing
2. centralized behaviour with regards to core configuration expectations

    """

    def __init__(self, conf: Config):
        """

        Parameters
        ----------
        conf => Config:
            Config loader instance which is used for all of the other methods,
            but is also meant to be made avaialble to the toolbox consumer.

        """
        self.config = conf

        self.prov = None
        """ will hold the provisioner """

    def run_bootstrap(self, name: str):
        """ Botstrap an MTT python package """
        eps = metadata.entry_points()[MTT_PACKAGE_BOOTSTRAP_ENTRYPOINT]
        for ep in eps:
            if ep.name == name:
                run_bootstrap = ep.load()
                return run_bootstrap(self)
        else:
            raise KeyError("Plugin not found {}.{}".format(type.value, name))

    def config(self) -> Config:
        """ Get the config object used by the toolbox instance """
        return self.config

    def provisioner(self):
        """

        Get/Make a provisioner based on config

        This method expects that there is configuration available that tells it
        how to load a provisioner

           provisioner.json: { "plugin": }

        Returns:

        A plugin object for the active provisioner for the toobox


        """
        if not self.prov:
            provisioner_config = self.config.load("provisioner")
            """ A LoadedConfig object with config for provisiner """
            name = provisioner_config.get("plugin")
            """ what provisioner plugin name is expected """

            logger.info("creating new provisioner on first request")
            self.prov = self.get_plugin(PluginType.PROVISIONER, name)

        return self.prov

    def get_plugin(self, type, name: str, *passed_args, **passed_kwargs):
        """ Allow plugin loading

        Parameters:

        type (str): type that matched the enumerator for types

            You can pass a case-insensitive key name such a "provisioner" or the
            plugin/entrypoint string "mirantis.testing.provisioner"

        Returns:
        a plugin object as defined by a python package factory for the matching
        type/key

        @see ./plugin.py -> plugins are to big a topic to discuss here

        """

        """ we do some argument conditioning as we don't expect complex imports"""
        if isinstance(type, str):
            for plugin in PluginType:
                if plugin.name.lower() == type.lower():
                    type = plugin
                    break
                if plugin.value.lower() == type.lower():
                    type = plugin
                    break
            else:
                logger.error("toolbox.get_plugin() didn't recognize the plugin type it was asked for: %s", type)
                raise KeyError("Unknown plugin type request: %s", type)


        return load_plugin(self.config, type, name, *passed_args, **passed_kwargs)
