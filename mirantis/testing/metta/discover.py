import os.path
import sys
import logging
import importlib.util
from typing import List

from configerus import new_config as configerus_new_config
from configerus.config import Config
from configerus.loaded import LOADED_KEY_ROOT
from configerus.contrib.files import PLUGIN_ID_SOURCE_PATH, CONFIGERUS_PATH_KEY
from configerus.contrib.dict import PLUGIN_ID_SOURCE_DICT, CONFIGERUS_DICT_DATA_KEY

from .plugin import METTA_PLUGIN_CONFIG_KEY_PLUGINID, METTA_PLUGIN_CONFIG_KEY_INSTANCEID, METTA_PLUGIN_CONFIG_KEY_PRIORITY

logger = logging.getLogger('metta.discover')

METTA_CONFIG_LABEL = 'metta'
""" this config label is used as a default for discovery from config """
METTA_CONFIG_SOURCES_KEY = 'config.sources'
""" This config key is used to find additional config sources to add """
METTA_CONFIG_IMPORTS_KEY = 'imports'
""" This config key is used to find modules to import """

METTA_ROOT_FILES = [
    'metta.yml',
    'metta.json'
]
""" The presence of any of these files could be used to mark a config source """

DEFAULT_SOURCE_PRIORITY = 40
""" Default priority for configerus path sources added when finding project root marker files """
DEFAULT_SOURCE_CONFIG_PRIORITY = 70
""" Default priority for configerus sources found in config """

DEFAULT_ENVIRONMENT_ROOT_CONFIG_IF_NO_ROOT_IS_FOUND = {
    'metta': {
        'environments': {
            'name': 'none'
        }
    }
}
""" If no root is found then this config is passed back as a data source """


def discover_project_root(config: Config, start_path: str,
                          marker_files: List[str] = METTA_ROOT_FILES):
    """ try to find a project root path

    We start looking in the start_path for certain marker files, and if we don't find
    any then we check the parent, recursively.

    If we never find a marker file then we assume that the current path is the
    root.

    """
    # standardize the path to rid of issues that could be cause by path tricks
    # such as  'path/..'
    start_path = os.path.realpath(start_path)

    # Try to any a path from start+path and up that contains a marker file as a
    # config source.
    check_path = start_path
    depth = 0
    while check_path:
        # if we are in a root path then stop scanning
        if check_path == os.path.dirname(check_path):
            break

        for ROOT_FILE in marker_files:
            root_file_path = os.path.join(check_path, ROOT_FILE)

            if os.path.isfile(root_file_path):
                # If we found a marker file in a path, then we add that path as
                # a config source.  If the path contains a ./config then we add
                # that as well.

                if check_path not in sys.path:
                    sys.path.append(check_path)

                priority = DEFAULT_SOURCE_PRIORITY - depth
                instance_id = "project{}".format(
                    "-{}".format(depth) if depth else '')
                config.add_source(
                    plugin_id=PLUGIN_ID_SOURCE_PATH,
                    instance_id=instance_id,
                    priority=priority).set_path(check_path)
                logger.info(
                    "Added project path as config: {} => {}".format(
                        check_path, instance_id))

                depth += 1
                break

        # move up one directory and try again
        check_path = os.path.dirname(check_path)

    if len(config.plugins) == 0:
        instance_id = "environment_none"
        logger.info(
            "No project config found, creating a dummy: {}".format(instance_id))
        config.add_source(
            plugin_id=PLUGIN_ID_SOURCE_DICT,
            instance_id=instance_id,
            priority=priority).set_data(DEFAULT_ENVIRONMENT_ROOT_CONFIG_IF_NO_ROOT_IS_FOUND)

    return config


def discover_sources_from_config(
        config: Config, label: str = METTA_CONFIG_LABEL, base: str = METTA_CONFIG_SOURCES_KEY):
    """ Discover more config sources by loading and processing config

    Run this is you want to add config sources to a config object as defined in config itself

    Parameters:
    -----------

    config (Config) : config object to scan, and to add sources to

    label (str) : config label to load to search for sources
    base (str) : config key that should contain the list of sources

    """
    metta_config = config.load(label)

    config_sources = metta_config.get(base)
    if config_sources is not None:
        for instance_id in config_sources.keys():
            instance_base = [base, instance_id]

            plugin_id = metta_config.get(
                [instance_base, METTA_PLUGIN_CONFIG_KEY_PLUGINID], exception_if_missing=True)
            priority = metta_config.get(
                [instance_base, METTA_PLUGIN_CONFIG_KEY_PRIORITY])

            if priority is None:
                priority = DEFAULT_SOURCE_CONFIG_PRIORITY

            logger.info(
                "Adding metta sourced config plugin: {}:{}".format(
                    plugin_id, instance_id))
            plugin = config.add_source(
                plugin_id=plugin_id,
                instance_id=instance_id,
                priority=priority)

            if plugin_id == PLUGIN_ID_SOURCE_PATH:
                source_path = metta_config.get(
                    [instance_base, 'path'], exception_if_missing=True)
                plugin.set_path(path=source_path)
            elif plugin_id == PLUGIN_ID_SOURCE_DICT:
                source_data = metta_config.get(
                    [instance_base, CONFIGERUS_DICT_DATA_KEY], exception_if_missing=True)
                plugin.set_data(data=source_data)


def discover_imports(config: Config, label: str = METTA_CONFIG_LABEL,
                     base: str = METTA_CONFIG_IMPORTS_KEY):
    """ Look in config for module imports

    Use this if you want to dynamically import some modules defined in config.
    This can be used to load custom plugins that are decorated by the plugin
    Factory, but can include any module by path.

    @NOTE Modules are loaded bt path, without a local namespace.

    Parameters:
    -----------

    config (Config) : config object to scan, and to add sources to

    label (str) : config label to load to search for sources
    base (str) : config key that should contain the list of sources

    """
    metta_config = config.load(label)

    imports_config = metta_config.get(base)
    if imports_config is not None:
        for import_name in imports_config:
            module_path = metta_config.get(
                [base, import_name, CONFIGERUS_PATH_KEY], exception_if_missing=True)
            if os.path.isdir(module_path):
                if path not in sys.path:
                    sys.path.append(path)
            elif os.path.isfile(module_path):
                spec = importlib.util.spec_from_file_location(
                    import_name, module_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                logger.debug(
                    "Loaded module: {} : {}".format(
                        import_name, module_path))
