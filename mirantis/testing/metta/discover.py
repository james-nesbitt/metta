import os.path
import sys
import logging

from configerus import new_config as configerus_new_config
from configerus.config import Config
from configerus.contrib.files import PLUGIN_ID_SOURCE_PATH
from configerus.contrib.dict import PLUGIN_ID_SOURCE_DICT

logger = logging.getLogger('metta.discover')

FIXED_CONFIGERUS_BOOSTRAPS = [
    "deep",
    "get",
    "jsonschema",
    "files"
]

DEFAULT_SOURCE_PRIORITY = 40
DEFAULT_SOURCE_CONFIG_PRIORITY = 70


def discover_metta_from_config(config: Config):
    """ Discover environments by looking for .metta """
    metta_config = config.load('metta')

    config_sources = metta_config.get('config.sources')
    if config_sources is not None:
        for source in config_sources:
            plugin_id = source['plugin_id']
            instance_id = source['instance_id'] if 'instance_id' in source else 'unnamed'
            priority = source['priority'] if 'priority' in source else DEFAULT_SOURCE_CONFIG_PRIORITY

            logger.info(
                "Adding metta sourced config plugin: {}:{}".format(
                    plugin_id, instance_id))
            plugin = config.add_source(
                plugin_id=plugin_id,
                instance_id=instance_id,
                priority=priority)

            if plugin_id == 'path':
                source_path = source['path']
                plugin.set_path(path=source_path)
            elif plugin_id == 'dict':
                source_data = source['data']
                plugin.set_data(data=source_data)


def discover_project_config(config: Config, start_path: str):
    """ try to find a project root path

    We start looking in the cwd for certain marker files, and if we don't find
    any then we check the parent, recursively.

    If we never find a marker file then we assume that the current path is the
    root.

    """

    METTA_ROOT_FILES = {
        'metta.yml'
    }

    # Try to add a path from cwd and up that contains a mettac.py file
    check_path = start_path
    depth = 0
    while check_path:
        # if we are in a root path then stop
        if check_path == '/':
            break

        for ROOT_FILE in METTA_ROOT_FILES:
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

                break

        # move up one directory and try again
        depth += 1
        check_path = os.path.dirname(check_path)

    if len(config.plugins) == 0:
        instance_id = "environment_none"
        logger.info(
            "No project config found, creating a dummy: {}".format(instance_id))
        config.add_source(plugin_id=PLUGIN_ID_SOURCE_DICT, instance_id=instance_id, priority=priority).set_data({
            'metta': {
                'environments': {
                    'name': 'none'
                }
            }
        })

    return config
