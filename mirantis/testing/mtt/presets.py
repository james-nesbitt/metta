import os.path
import logging
import pkg_resources

from configerus.config import Config as configerus_Config
from configerus.contrib.dict import PLUGIN_ID_SOURCE_DICT as CONFIGERUS_SOURCE_DICT
from configerus.contrib.files import PLUGIN_ID_SOURCE_PATH as CONFIGERUS_SOURCE_PATH

logger = logging.getLogger("mtt.presets")

MTT_PRESET_CONFIG_LABEL = "mtt"
""" This config label will be loaded to interpret config in add_preset_config """
MTT_CONFIG_PATH = pkg_resources.resource_filename(
    "mirantis.testing.mtt", "config")
""" Path to the MTT Mirantis config preset configurations """
MTT_CONFIG_SOURCE_INSTANCE_ID_PREFIX = "mtt_preset"
""" All config that we add here will have its source instance_id prefixed with this """
MTT_CONFIG_CONFIG_PRESET_BASE = 'presets'
""" preset configuration will be found under this config .get() key """
MTT_PRESETS = [
    ("variation", pkg_resources.resource_filename(
        "mirantis.testing.mtt", "config/variation")),
    ("cluster", pkg_resources.resource_filename(
        "mirantis.testing.mtt", "config/cluster")),
    ("platform", pkg_resources.resource_filename(
        "mirantis.testing.mtt", "config/platform")),
    ("release", pkg_resources.resource_filename(
        "mirantis.testing.mtt", "config/release"))
]
""" List of available presets that you can include in load("mtt").get('presets')
    (key, preset_root_path):
        key: config key that will find the preset value under the base value
            from MTT_CONFIG_CONFIG_PRESET_BASE
        path: preset root path that should contains a path matching the value
            which will be added as a source config path
"""
MTT_PRESET_DEFAULT_PRIORITY = 70
""" Default priority to use for preset config sources """


def add_preset_config(config: configerus_Config,
                      priority=MTT_PRESET_DEFAULT_PRIORITY):
    """ Read mtt config and interpret it for modifying the config

    Interprests config.load("mtt") to determine if any `presets` config
    sources should be added.

    The following presets are currently available:

    1. variation : see ./config/variations : kind of access to a larger config
        pattern that we use at Mirantis.  An example is `ltc` which refers to
        using launchpad & terraform with our common config.

    2. cluster : @see ./config/cluster : config for different cluster sizes
    3. release : @see ./config/release : config for different mirantis product
        releases
    4. platform : @see ./config/platform : config for different os platforms

    In all cases, the pattern is that a key from config.load("mtt") is
    used to pull a preset name, and the matching preset subpath is added to the
    config object as a path source.

    The presets for #2, #3 and # are focused on overriding `variables` (label)
    which should be consumed by whichever variation you use.

    Parameter:
    ----------

    config (configerus.config.Config) : a configerus Config object which will
        have config sources added

    priority (int) : optionally override the source plugin priority.

    Throws:
    -------

    Can throw a KeyError if a preset id requested that does not exist

    """

    # Now we start to process `presets`
    # To do this we load the `mtt` config label and look for preset
    # keys in the loaded config.
    # For each preset key found we try to add a path config source for the
    # value
    mtt_config = config.load(MTT_PRESET_CONFIG_LABEL)

    for preset in MTT_PRESETS:
        # For each of the available presets, look in the loaded mtt
        # config for values matching the preset key.  if the key is found then
        # we try to match a path in the mtt/config/{key}/{value}
        # and add the path as a config source.

        (preset_key, preset_root_path) = preset
        preset_value = mtt_config.get(
            [MTT_CONFIG_CONFIG_PRESET_BASE, preset_key], exception_if_missing=False)
        if preset_value:
            preset_instance_id = "{}-{}-{}".format(
                MTT_CONFIG_SOURCE_INSTANCE_ID_PREFIX, preset_key, preset_value)
            # quick check to see if we've already added this preset.
            if not config.has_source(preset_instance_id):
                # build a preset config path and add it as a source if it
                # exists
                preset_full_path = os.path.join(preset_root_path, preset_value)
                if os.path.isdir(preset_full_path):
                    logger.debug(
                        "Using MTT preset {}:{} => {}".format(
                            preset_key, preset_value, preset_full_path))
                    config.add_source(
                        CONFIGERUS_SOURCE_PATH,
                        preset_instance_id,
                        priority).set_path(preset_full_path)
                else:
                    raise KeyError(
                        "mtt doesn't have a preset '%s:%s'",
                        preset_key,
                        preset_value)

        else:
            logger.debug("No MTT preset selected for {}".format(preset_key))
