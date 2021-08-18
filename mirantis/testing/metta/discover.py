"""

DISCOVER: Functionality for discovering METTA environments.

Discover is respondible for discovering project roots and initial project
configuration, along with related configuration, dependency injections and
fixtures.

"""
import os.path
import sys
import logging
from typing import List

from configerus.plugin import Type as ConfigerusType
from configerus.config import Config
from configerus.contrib.files import PLUGIN_ID_SOURCE_PATH

logger = logging.getLogger("metta.discover")

METTA_CONFIG_LABEL = "metta"
""" this config label is used as a default for discovery from config """
METTA_CONFIG_SOURCES_KEY = "config.sources"
""" This config key is used to find additional config sources to add """
METTA_CONFIG_IMPORTS_KEY = "imports"
""" This config key is used to find modules to import """

METTA_ROOT_FILES = ["metta.yml", "metta.json"]
""" The presence of any of these files could be used to mark a conf source """

DEFAULT_SOURCE_PRIORITY = 40
""" Default priority for configerus path sources for root marker files """
DEFAULT_SOURCE_CONFIG_PRIORITY = 70
""" Default priority for configerus sources found in config """

DEFAULT_ENVIRONMENT_ROOT_CONFIG_IF_NO_ROOT_IS_FOUND = {
    "metta": {"project": {"name": "none"}},
    "environments": {"missing": {}},
}
""" If no root is found then this config is passed back as a config source """


def discover_project_root(config: Config, start_path: str, marker_files: List[str] = None):
    """Find a project root path.

    We start looking in the start_path for certain marker files, and if we
    don't find any then we check the parent, recursively. If we never find a
    marker file then we assume that the current path is the root.

    Whichever path we think is the root, we add a a configerus path source.
    That means that you can put whatever you want there for config.

    Commonly, one used just the metta.yml|json file to direct metta to include
    additional paths (such a ./config) from the metta.yml path.

    """
    if marker_files is None:
        marker_files = METTA_ROOT_FILES

    # standardize the path to rid of issues that could be cause by path tricks
    # such as  'path/..'
    start_path = os.path.realpath(start_path)

    # Try to any a path from start+path and up that contains a marker file as a
    # config source.
    check_path = start_path
    depth = 0
    while check_path:
        # if we are in a system /root path then stop scanning
        # we do this by checking if the path's parent is the
        # same as itself.
        if check_path == os.path.dirname(check_path):
            break

        for root_file in marker_files:
            root_file_path = os.path.join(check_path, root_file)

            if os.path.isfile(root_file_path):
                # If we found a marker file in a path, then we add that path as
                # a config source.
                if check_path not in sys.path:
                    sys.path.append(check_path)

                priority = DEFAULT_SOURCE_PRIORITY - depth
                if depth:
                    instance_id = f"project-{depth}"
                else:
                    instance_id = "project"
                config.add_source(
                    plugin_id=PLUGIN_ID_SOURCE_PATH,
                    instance_id=instance_id,
                    priority=priority,
                ).set_path(check_path)
                logger.info("Added project path as config: %s => %s", check_path, instance_id)

                depth += 1

                # Since we already added this path as a config source, we don't
                #  need to keep looking for more files.
                break

        # move up one directory and try again
        check_path = os.path.dirname(check_path)

    try:
        config.plugins.get_plugins(type=ConfigerusType.SOURCE)
    except KeyError:
        logger.warning("No project config found")

    return config
