
import logging
import appdirs
import pkg_resources
from .config import Config
from .plugin import load_plugin, PluginType
from .config_sources import SourceList
from typing import List, Dict, Any
import os.path
from importlib import metadata

MTT_BOOTSTRAP_ENTRYPOINT = "mirantis.testing.toolbox.bootstrap"
""" setuptools entry_point target for module bootstrapping """

MTT_TOOLBOX_APP_NAME = "mtt"
""" app name, which is used in formation of paths for things like user config """

MTT_TOOLBOX_CORECONFIG_LABEL = "config"
""" Config.load() target which can contain core config that affects construction """

MTT_PATHS_SYSTEM_PRIORITY = 15
MTT_PATHS_ADDITIONAL_PRIORITY = 55

logger = logging.getLogger("mirantis.testing.toolbox:init")

_mtt_toolbox = None
""" Global toolbox object used for MTT module management and boostrapping (created below)"""

def new_sources():
    """ make a source handler object

    It's complex to parametrize sources, so a SourceList object gives a handler to add
    sources one at a time.

    Return:

    Empty SourceList handler.  Use this to build a config source list that you can
    then pass to config_from_source_list for a proper Config object
    """
    return SourceList()

def config_from_source_list(sources: SourceList, include_default_config_paths: bool=True):
    """
    Config factory

    Try to build a new config object comprehensibely.  This means that you first must create a
    SourceList object, which will be used to tell the config object where it can get config data
    and how to prioritize sources.

    Parameters
    ----------
    sources (SourceList): source form which to pull config data

    additional_config_values (Dict[str, str]): Fixed Dict of config to add to the
        config object.  This allows a non-files based source

    Returns:

    A prepared Config object loaded with the specified paths

    """

    logger.info("Creating new toolbox object from settings")

    assert isinstance(sources, SourceList), "Passed SourceList is not valid : {}".format(sources)

    if include_default_config_paths:
        #this package contains default sane config
        sources.add_filepath_source(pkg_resources.resource_filename("mirantis.testing.toolbox", "files/config"), "toolbox", MTT_PATHS_SYSTEM_PRIORITY)

        # a user config path (like ~/.config/mtt) may contain config
        user_conf_path = appdirs.user_config_dir(MTT_TOOLBOX_APP_NAME)
        if os.path.exists(user_conf_path):
            sources.add_filepath_source("user", user_conf_path, MTT_PATHS_SYSTEM_PRIORITY)

    config = Config(sources=sources)

    # Here we want to allow some deep core configuration to come from the
    # config files themselves, so we allow an mtt.yaml|json file to
    # further instruct to us how to proceed

    try:
        mtt_config = config.load("mtt")
    except KeyError as e:
        # Ignore if the mtt config cannot be found
        pass

    else:
        # allow a config.yaml file to define more config paths
        addl_paths = mtt_config.get("paths", exception_if_missing=False)
        if addl_paths:
            for path in addl_paths:
                if isinstance(path, str):
                    sources.add_filepath_source(str)
                if isinstance(path, dict):
                    try:
                        path = path["path"]
                        key = path["key"] if "key" in path else ""
                        priority = path["priority"] if "priority" in path else MTT_PATHS_ADDITIONAL_PRIORITY
                        sources.add_filepath_source(path, key, priority)
                    except:
                        logger.warn("Could not load additional config path as it was not interpreted propely: %s", path)
                        pass

            # mtt_config could now be out of date, so we reload it
            mtt_config = config.load("mtt", True)

        # boostrap any modules config tells us to boostrap
        modules = mtt_config.get("modules", exception_if_missing=False)
        if modules:
            try:
                eps = metadata.entry_points()[MTT_BOOTSTRAP_ENTRYPOINT]
                for ep in eps:
                    if ep.name in modules:
                        plugin = ep.load()
                        plugin(config)
                        modules.remove(ep.name)

            except KeyError as e:
                logger.error("No boostrapper entry_points are defined by any python packages")

            if len(modules):
                raise ValueError("Modules not found for boostrapping not found {}".format(modules))




    return config

def provisioner_from_config(config: Config):
    """ Build a provisioner plugin from a config handler

    Parameters:

    config (Config): prepared config object which will be used to load provisioner
        configuration


    Return:

    provisioner plugin object
    """

    provisioner_config = config.load("provisioner")
    """ A LoadedConfig object with config for provisiner """
    name = provisioner_config.get("plugin")
    """ what provisioner plugin name is expected """

    logger.info("creating new provisioner on first request")
    return get_plugin(type=PluginType.PROVISIONER, name=name, config=config)


def get_plugin(type, name: str, config: Config, *passed_args, **passed_kwargs):
    """ Allow plugin loading

    Parameters:

    type (PluginType|str): type that matched the enumerator for types

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


    return load_plugin(config, type, name, *passed_args, **passed_kwargs)
