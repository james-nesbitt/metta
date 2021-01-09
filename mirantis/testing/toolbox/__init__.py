
import logging
import appdirs
import pkg_resources
from .config import Config
from .plugin import load_plugin, PluginType
from .toolbox import Toolbox
from .config_sources import SourceList
from collections import OrderedDict
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
    """ make a source handler object """
    return SourceList()

def toolbox_from_settings(conf_sources: SourceList=None, additional_config_values: Dict[str, Any]={}, include_default_config_paths: bool=True):
    """
    Toolbox factory

    Parameters
    ----------
    wd -> str:
        working directory of the project which is using the toolbox

    additional_conf_paths -> List[(str[, str[, int]])]:
        additional string full paths that can be used to load config, in
        ascending order of priority
        The list of arguments is a set of tuples:
        (
            string path: the string path to be used
            string key: optional key for the path for string replacement
            int priority: ordering priority for the added paths
        )

        the toolbox will always look in the passed wd (if not empty) and in
        a user config folder for mtt if you don't pass
        use_default_config_paths=False

    Returns:

    A prepared Config object loaded with the specified paths

    """

    logger.info("Creating new toolbox object from settings")

    if include_default_config_paths:
        #this package contains default sane config
        conf_sources.add_filepath_source(pkg_resources.resource_filename("mirantis.testing.toolbox", "files/config"), "toolbox", MTT_PATHS_SYSTEM_PRIORITY)

        # a user config path (like ~/.config/mtt) may contain config
        user_conf_path = appdirs.user_config_dir(MTT_TOOLBOX_APP_NAME)
        if os.path.exists(user_conf_path):
            conf_sources.add_filepath_source("user", user_conf_path, MTT_PATHS_SYSTEM_PRIORITY)

    config = config_from_settings(sources=conf_sources,additional_values=additional_config_values)
    toolbox = Toolbox(config)

    # Here we want to allow some deep core configuration to come from the
    # config files themselves, so we allow a config.yaml|json file to
    # further instruct to us how to proceed

    config_config = config.load("config")


    # allow a config.yaml file to define more config paths
    addl_paths = config_config.get("mtt.conf.paths", exception_if_missing=False)
    if addl_paths:
        for path in addl_paths:
            if isinstance(path, str):
                toolbox.config.add_path(str)
            if isinstance(path, dict):
                try:
                    path = path["path"]
                    key = path["key"] if "key" in path else ""
                    priority = path["priority"] if "priority" in path else MTT_PATHS_ADDITIONAL_PRIORITY
                    toolbox.config.add_path(str, key, path)
                except:
                    logger.warn("Could not load additional config path as it was not interpreted propely: %s", path)
                    pass


    # try:
    # boostrap any modules config tells us to boostrap
    modules = config_config.get("mtt.conf.modules", exception_if_missing=False)
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

    # Now make the toolbox
    return toolbox

def config_from_settings(sources: SourceList=None, additional_values: Dict = {}):
    """ Config factory """

    logger.info("Creating new config object from settings")
    return config.Config(sources=sources, additional_values=additional_values)
