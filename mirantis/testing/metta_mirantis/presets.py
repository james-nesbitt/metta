import os.path
import logging
import pkg_resources

from configerus.contrib.files import PLUGIN_ID_SOURCE_PATH
from configerus.contrib.dict import PLUGIN_ID_SOURCE_DICT
from mirantis.testing.metta.environment import Environment

logger = logging.getLogger("metta_mirantis.presets")

METTA_PRESET_CONFIG_LABEL = "metta_mirantis"
""" This config label will be loaded to interpret config in add_preset_config """
METTA_CONFIG_SOURCE_INSTANCE_ID_PREFIX = "metta_mirantis-preset"
""" All config that we add here will have its source instance_id prefixed with this """
METTA_CONFIG_CONFIG_PRESET_BASE = 'presets'
""" preset configuration will be found under this config .get() key """
METTA_PRESET_DEFAULT_PRIORITY = 60
""" Default priority to use for preset config sources """
METTA_PRESET_PACKAGE = 'mirantis.testing.metta_mirantis'


def preset_config():
    """ List of available presets that you can include in load("metta").get('presets')
        (key, preset_root_path):
            key: config key that will find the preset value under the base value
                from METTA_CONFIG_CONFIG_PRESET_BASE
            path: preset root path that should contains a path matching the value
                which will be added as a source config path
            priority delta: preset relative priority compared to other presets
    """
    return [
        ("variation", pkg_resources.resource_filename(
            METTA_PRESET_PACKAGE, "config/variation"), 0),
        ("cluster", pkg_resources.resource_filename(
            METTA_PRESET_PACKAGE, "config/cluster"), 1),
        ("platform", pkg_resources.resource_filename(
            METTA_PRESET_PACKAGE, "config/platform"), 1),
        ("release", pkg_resources.resource_filename(
            METTA_PRESET_PACKAGE, "config/release"), 1)
    ]


def add_preset_config(environment: Environment,
                      priority=METTA_PRESET_DEFAULT_PRIORITY):
    """ Read metta config and interpret it for modifying the config

    Interprests config.load("metta") to determine if any `presets` config
    sources should be added.

    The following presets are currently available:

    1. variation : see ./config/variations : kind of access to a larger config
        pattern that we use at Mirantis.  An example is `lat` which refers to
        using launchpad & terraform with our common config.

    2. cluster : @see ./config/cluster : config for different cluster sizes
    3. release : @see ./config/release : config for different mirantis product
        releases
    4. platform : @see ./config/platform : config for different os platforms

    In all cases, the pattern is that a key from config.load("metta") is
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
    # To do this we load the `metta` config label and look for preset
    # keys in the loaded config.
    # For each preset key found we try to add a path config source for the
    # value
    try:
        metta_config = environment.config.load(METTA_PRESET_CONFIG_LABEL)
    except KeyError:
        logger.debug("metta Presets found no usable config")
        return

    for preset in preset_config():
        # For each of the available presets, look in the loaded metta
        # config for values matching the preset key.  if the key is found then
        # we try to match a path in the metta/config/{key}/{value}
        # and add the path as a config source.

        (preset_key, preset_root_path, preset_priority_delta) = preset
        preset_priority = priority + preset_priority_delta
        preset_value = metta_config.get(
            [METTA_CONFIG_CONFIG_PRESET_BASE, preset_key], exception_if_missing=False)

        if preset_value:
            preset_instance_id = "{}-{}-{}".format(
                METTA_CONFIG_SOURCE_INSTANCE_ID_PREFIX, preset_key, preset_value.replace('/', '_'))
            # quick check to see if we've already added this preset.
            if not environment.config.has_source(preset_instance_id):
                # build a preset config path and add it as a source if it
                # exists
                preset_full_path = os.path.join(preset_root_path, preset_value)
                if os.path.isdir(preset_full_path):
                    logger.debug(
                        "Using metta preset {}:{} => {}".format(
                            preset_key, preset_value, preset_full_path))
                    environment.config.add_source(
                        PLUGIN_ID_SOURCE_PATH,
                        preset_instance_id,
                        preset_priority).set_path(preset_full_path)
                else:
                    raise KeyError(
                        "metta doesn't have a preset '%s:%s'",
                        preset_key,
                        preset_value)

        else:
            logger.debug("No metta preset selected for {}".format(preset_key))
