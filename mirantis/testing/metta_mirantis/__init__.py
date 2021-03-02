"""

metta Mirantis


"""

import logging

from mirantis.testing.metta.plugin import Factory, Type
from mirantis.testing.metta.environment import Environment

from .common import add_common_config
from .presets import add_preset_config

from .plugins.mke_client import MKEAPIClientPlugin
from .plugins.msr_client import MSRAPIClientPlugin

""" PLugin factories """

METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID = 'metta_mirantis_client_mke'
""" Mirantis MKE API Client plugin id """


@Factory(type=Type.CLIENT, plugin_id=METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID)
def metta_mirantis_plugin_factory_client_mke(
        environment: Environment, instance_id: str = ""):
    """ Create a Mirantis MKE API Client """
    return MKEAPIClientPlugin(environment, instance_id)


METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID = 'metta_mirantis_client_msr'
""" Mirantis MSR APIP Client plugin id """


@Factory(type=Type.CLIENT, plugin_id=METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID)
def metta_mirantis_plugin_factory_client_msr(
        environment: Environment, instance_id: str = ''):
    """ Create a Mirantis MSR API Client """
    return MSRAPIClientPlugin(environment, instance_id)


""" METTA bootstraps that we will use on config objects """


def bootstrap_common(environment: Environment):
    """ metta configerus bootstrap

    Add some Mirantis specific config options for presets

    Additional config sources may be added based on config.load("metta")
    which will try to add config for metta `presets`
    This gives access to "variation", "cluster", "platform" and "release"
    presets.  You can dig deeper, but it might implicitly make sense if you look
    at the config folder of this module.

    @see .common.add_common_config() for details

    """
    add_common_config(environment)


def bootstrap_presets(environment: Environment):
    """ metta configerus bootstrap

    Add some Mirantis specific config options for presets

    Additional config sources may be added based on config.load("metta")
    which will try to add config for metta `presets`
    This gives access to "variation", "cluster", "platform" and "release"
    presets.  You can dig deeper, but it might implicitly make sense if you look
    at the config folder of this module.

    @see .presets.add_preset_config() for details

    """
    add_preset_config(environment)
