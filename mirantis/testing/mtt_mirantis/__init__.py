"""

MTT Mirantis


"""

import os.path
import pkg_resources

from mirantis.testing.mtt import plugin as mtt_plugin
from mirantis.testing.mtt.config import Config

import mirantis.testing.mtt_common as mtt_common

from .plugins.launchpad import LaunchpadProvisionerPlugin

MTT_LAUNCHPAD_PROVISIONER_PLUGIN_ID = 'mtt_launchpad'
""" provisioner plugin_id for the launchpad plugin """
@mtt_plugin.Factory(type=mtt_plugin.Type.PROVISIONER, plugin_id=MTT_LAUNCHPAD_PROVISIONER_PLUGIN_ID)
def mtt_plugin_factory_provisioner_dummy(config: Config, instance_id: str = ''):
    """ create an mtt provisionersss dict plugin """
    return LaunchpadProvisionerPlugin(config, instance_id)


MTT_MIRANTIS_CONFIG_LABEL = 'mtt_mirantis'
""" This config label will be loaded to interpret config in config_interpret_mtt_mirantis """
MTT_MIRANTIS_CONFIG_CLUSTER_KEY = 'cluster'
""" Config key which will give us cluster to load """
MTT_MIRANTIS_CONFIG_VARIATION_KEY = 'variation'
""" Config key which will give us variation to load """
MTT_MIRANTIS_CONFIG_RELEASE_KEY = 'release'
""" Config key which will give us release to load """
MTT_MIRANTIS_CONFIG_PLATFORM_KEY = 'platform'
""" Config key which will give us platform to load """
MTT_MIRANTIS_PATH=pkg_resources.resource_filename('mirantis.testing.mtt_mirantis', '.')
""" Path to the mtt_mirantis project root """
MTT_MIRANTIS_CONFIG_PATH=pkg_resources.resource_filename('mirantis.testing.mtt_mirantis', 'config')
""" Path to the MTT Mirantis config preset configurations """
MTT_MIRANTIS_CONFIG_PREFIX = 'mtt_mirantis_config'
""" All config that we add here will have its source instance_id prefixed with this """
MTT_MIRANTIS_CONFIG_CLUSTER_PATH = pkg_resources.resource_filename('mirantis.testing.mtt_mirantis', 'config/cluster')
""" Subpath in config folder that contains cluster folders """
MTT_MIRANTIS_CONFIG_VARIATION_PATH = pkg_resources.resource_filename('mirantis.testing.mtt_mirantis', 'config/variation')
""" Subpath in config folder that contains variation folders """
MTT_MIRANTIS_CONFIG_RELEASE_PATH = pkg_resources.resource_filename('mirantis.testing.mtt_mirantis', 'config/release')
""" Subpath in config folder that contains release folders """
MTT_MIRANTIS_CONFIG_PLATFORM_PATH = pkg_resources.resource_filename('mirantis.testing.mtt_mirantis', 'config/platform')
""" Subpath in config folder that contains platform folders """

def config_interpret_mtt_mirantis(config:Config):
    """ Read mtt_mirantis config and interpret it for modifying the config """

    mtt_mirantis_paths_instance_id = "{}-paths".format(MTT_MIRANTIS_CONFIG_PREFIX)
    if not config.has_source(mtt_mirantis_paths_instance_id):
        config.add_source(mtt_common.MTT_PLUGIN_ID_CONFIGSOURCE_DICT, mtt_mirantis_paths_instance_id).set_data({
            config.paths_label(): {
                'mtt_mirantis': MTT_MIRANTIS_PATH
            }
        })

    mtt_mirantis_common_instance_id = MTT_MIRANTIS_CONFIG_PREFIX
    if not config.has_source(mtt_mirantis_common_instance_id):
        config.add_source(mtt_common.MTT_PLUGIN_ID_CONFIGSOURCE_PATH, mtt_mirantis_common_instance_id).set_path(MTT_MIRANTIS_CONFIG_PATH)

    mtt_mirantis_config = config.load(MTT_MIRANTIS_CONFIG_LABEL)

    cluster = mtt_mirantis_config.get(MTT_MIRANTIS_CONFIG_CLUSTER_KEY, exception_if_missing=False)
    if cluster:
        cluster_path = os.path.join(MTT_MIRANTIS_CONFIG_CLUSTER_PATH, cluster)
        try:
            _config_add_mirantis_preset(config, cluster, cluster_path)
        except KeyError as e:
            raise KeyError("Requested MTT_Mirantis config variation not found: %s", cluster)

    variation = mtt_mirantis_config.get(MTT_MIRANTIS_CONFIG_VARIATION_KEY, exception_if_missing=False)
    if variation:
        variation_path = os.path.join(MTT_MIRANTIS_CONFIG_VARIATION_PATH, variation)
        try:
            _config_add_mirantis_preset(config, variation, variation_path)
        except KeyError as e:
            raise KeyError("Requested MTT_Mirantis config variation not found: %s", variation)

    release = mtt_mirantis_config.get(MTT_MIRANTIS_CONFIG_RELEASE_KEY, exception_if_missing=False)
    if release:
        release_path = os.path.join(MTT_MIRANTIS_CONFIG_RELEASE_PATH, release)
        try:
            _config_add_mirantis_preset(config, release, release_path)
        except KeyError as e:
            raise KeyError("Requested MTT_Mirantis config release not found: %s", release)

    platform = mtt_mirantis_config.get(MTT_MIRANTIS_CONFIG_PLATFORM_KEY, exception_if_missing=False)
    if platform:
        platform_path = os.path.join(MTT_MIRANTIS_CONFIG_PLATFORM_PATH, platform)
        try:
            _config_add_mirantis_preset(config, platform, platform_path)
        except KeyError as e:
            raise KeyError("Requested MTT_Mirantis config platform not found: %s", platform)


def _config_add_mirantis_preset(config:Config, preset:str, preset_path:str):
    """ Use one of the mirantis config presets

    This functions by adding one of the config folders in this modules as a
    config source if is hasn't already been added.

    """

    if os.path.isdir(preset_path):
        preset_instance_id = '{}-{}'.format(MTT_MIRANTIS_CONFIG_PREFIX, preset)
        preset_priority = config.default_priority() - 5
        if not config.has_source(preset_instance_id):
            config.add_source(mtt_common.MTT_PLUGIN_ID_CONFIGSOURCE_PATH, preset_instance_id, preset_priority).set_path(preset_path)
    else:
        raise KeyError("mtt_mirantis doesn't have a preset '%s'", preset)
