"""

Interact and manipulate Configerus objects.

"""
import logging
from typing import Any, List, Union

from configerus.config import Config
from configerus.loaded import LOADED_KEY_ROOT
from configerus.contrib.files import PLUGIN_ID_SOURCE_PATH, CONFIGERUS_PATH_KEY
from configerus.contrib.dict import PLUGIN_ID_SOURCE_DICT, CONFIGERUS_DICT_DATA_KEY
from configerus.contrib.env import (
    PLUGIN_ID_SOURCE_ENV_SPECIFIC,
    CONFIGERUS_ENV_SPECIFIC_BASE_KEY,
    PLUGIN_ID_SOURCE_ENV_JSON,
    CONFIGERUS_ENV_JSON_ENV_KEY,
)

from .globals import global_config

logger = logging.getLogger("metta.config")

DEFAULT_SOURCE_PRIORITY = 75
"""Default source plugin priority if not explicitly given."""

METTA_CONFIG_CONFIG_SOURCE_KEY = "config.sources"
"""Configerus config .get() key used to find config source definitions."""


def default_config(additional_bootstraps: List[str] = None):
    """Provide a global config object, creating one if needed."""
    config = global_config

    if additional_bootstraps is not None:
        for bootstrap_entrypoint_id in additional_bootstraps:
            logger.debug("bootstrapping: %s", bootstrap_entrypoint_id)
            config.bootstrap(bootstrap_entrypoint_id)

    return config


def add_config_sources_from_config(
    config: Config,
    label: str = "config",
    base: Union[str, List[Any]] = LOADED_KEY_ROOT,
    default_source_priority: int = DEFAULT_SOURCE_PRIORITY,
):
    """Add more config sources based on in config settings.
    Read some config which will tell us where more config can be found.
    This lets us use config to extend config, and is what make metta
    entirely extensible from a single metta.yml file.
    In the trade-off battle between configurable and convention, this leans
    heavily towards configuration, but it easily lends to standards.
    Parameters:
    -----------
    label (str) : configurus load label.
    base (str|List[str]) : configerus get key as a base for retrieving all
        config settings.
    """
    config_environment = config.load(label)
    config_sources = config_environment.get(base, default={})

    for instance_id in config_sources.keys():
        instance_base = [base, instance_id]

        # Keep in mind that the following plugin metadata is about
        # configerus plugins, not metta plugins.

        plugin_id = config_environment.get([instance_base, "plugin_id"])
        priority = config_environment.get(
            [instance_base, "priority"], default=default_source_priority
        )

        logger.debug(
            "Adding metta sourced config plugin: %s:%s",
            plugin_id,
            instance_id,
        )
        plugin = config.add_source(plugin_id=plugin_id, instance_id=instance_id, priority=priority)

        # Configerus plugins all work differently so we take a different
        # approach per plugin
        if plugin_id == PLUGIN_ID_SOURCE_PATH:
            path = config_environment.get([instance_base, CONFIGERUS_PATH_KEY])
            plugin.set_path(path=path)
        elif plugin_id == PLUGIN_ID_SOURCE_DICT:
            data = config_environment.get([instance_base, CONFIGERUS_DICT_DATA_KEY])
            plugin.set_data(data=data)
        elif plugin_id == PLUGIN_ID_SOURCE_ENV_SPECIFIC:
            source_base = config_environment.get([instance_base, CONFIGERUS_ENV_SPECIFIC_BASE_KEY])
            plugin.set_base(base=source_base)
        elif plugin_id == PLUGIN_ID_SOURCE_ENV_JSON:
            source_env = config_environment.get([instance_base, CONFIGERUS_ENV_JSON_ENV_KEY])
            plugin.set_env(env=source_env)
        # this should probably be a configerus standard
        elif hasattr(plugin, "set_data"):
            data = config_environment.get([instance_base, "data"])
            plugin.set_data(data=data)
        else:
            logger.warning(
                "had no way of configuring new Configerus source plugin %s",
                plugin_id,
            )
