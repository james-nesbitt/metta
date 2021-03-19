"""

metta Mirantis


"""

import logging
from typing import List, Dict

from mirantis.testing.metta.plugin import Factory, Type
from mirantis.testing.metta.environment import Environment

from .common import add_common_config
from .presets import add_preset_config

from .mke_client import MKEAPIClientPlugin, MKEAPICliPlugin, METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID
from .msr_client import MSRAPIClientPlugin, MSRAPICliPlugin, METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID

""" Plugin factories """


@Factory(type=Type.CLIENT, plugin_id=METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID)
def metta_mirantis_plugin_factory_client_mke(
        environment: Environment, instance_id: str = "", accesspoint: str = '', username: str = '', password: str = '', hosts: List[Dict] = []):
    """ Create a Mirantis MKE API Client """
    return MKEAPIClientPlugin(environment, instance_id, accesspoint=accesspoint,
                              username=username, password=password, hosts=hosts)


@Factory(type=Type.CLI, plugin_id=METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID)
def metta_terraform_factory_cli_mke(
        environment: Environment, instance_id: str = ''):
    """ create an MKE cli plugin """
    return MKEAPICliPlugin(environment, instance_id)


@Factory(type=Type.CLIENT, plugin_id=METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID)
def metta_mirantis_plugin_factory_client_msr(
        environment: Environment, instance_id: str = '', accesspoint: str = '', username: str = '', password: str = '', hosts: List[Dict] = []):
    """ Create a Mirantis MSR API Client """
    return MSRAPIClientPlugin(environment, instance_id, accesspoint=accesspoint,
                              username=username, password=password, hosts=hosts)


@Factory(type=Type.CLI, plugin_id=METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID)
def metta_terraform_factory_cli_msr(
        environment: Environment, instance_id: str = ''):
    """ create an MSR cli plugin """
    return MSRAPICliPlugin(environment, instance_id)


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


__all__ = [
    bootstrap_common,
    bootstrap_presets,
    METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID,
    METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID]
