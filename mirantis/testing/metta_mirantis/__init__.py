"""

Metta Mirantis.

Common components and configuration which are nice to use
when using metta with Mirantis products.

THese are entirely optional, but it makes a lot of
operations easier.

"""

from typing import List, Dict

from mirantis.testing.metta.plugin import Factory
from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.client import METTA_PLUGIN_INTERFACE_ROLE_CLIENT
from mirantis.testing.metta.healthcheck import METTA_PLUGIN_INTERFACE_ROLE_HEALTHCHECK
from mirantis.testing.metta_cli.base import METTA_PLUGIN_INTERFACE_ROLE_CLI

from .common import add_common_config
from .presets import add_preset_config

from .mke_client import (
    MKEAPIClientPlugin,
    METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID,
    METTA_MIRANTIS_MKE_BUNDLE_PATH_DEFAULT,
)
from .mke_cli import MKEAPICliPlugin, METTA_MIRANTIS_CLI_MKE_PLUGIN_ID
from .msr_client import (
    MSRAPIClientPlugin,
    METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID,
)
from .msr_cli import MSRAPICliPlugin, METTA_MIRANTIS_CLI_MSR_PLUGIN_ID

# ----- Plugin factories -----


# pylint: disable=too-many-arguments
@Factory(
    plugin_id=METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID,
    interfaces=[
        METTA_PLUGIN_INTERFACE_ROLE_CLIENT,
        METTA_PLUGIN_INTERFACE_ROLE_HEALTHCHECK,
        METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID,
    ],
)
def metta_mirantis_plugin_factory_client_mke(
    environment: Environment,
    instance_id: str = "",
    accesspoint: str = "",
    username: str = "",
    password: str = "",
    hosts: List[Dict] = None,
    bundle_root: str = METTA_MIRANTIS_MKE_BUNDLE_PATH_DEFAULT,
) -> MKEAPIClientPlugin:
    """Create a Mirantis MKE API Client."""
    return MKEAPIClientPlugin(
        environment,
        instance_id,
        accesspoint=accesspoint,
        username=username,
        password=password,
        hosts=hosts,
        bundle_root=bundle_root,
    )


@Factory(
    plugin_id=METTA_MIRANTIS_CLI_MKE_PLUGIN_ID,
    interfaces=[METTA_PLUGIN_INTERFACE_ROLE_CLI],
)
def metta_terraform_factory_cli_mke(
    environment: Environment, instance_id: str = ""
) -> MKEAPICliPlugin:
    """Create an MKE cli plugin."""
    return MKEAPICliPlugin(environment, instance_id)


# pylint: disable=too-many-arguments
@Factory(
    plugin_id=METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID,
    interfaces=[
        METTA_PLUGIN_INTERFACE_ROLE_CLIENT,
        METTA_PLUGIN_INTERFACE_ROLE_HEALTHCHECK,
        METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID,
    ],
)
def metta_mirantis_plugin_factory_client_msr(
    environment: Environment,
    instance_id: str = "",
    accesspoint: str = "",
    username: str = "",
    password: str = "",
    hosts: List[Dict] = None,
    protocol: str = "https",
):
    """Create a Mirantis MSR API Client."""
    return MSRAPIClientPlugin(
        environment,
        instance_id,
        accesspoint=accesspoint,
        username=username,
        password=password,
        hosts=hosts,
        protocol=protocol,
    )


@Factory(
    plugin_id=METTA_MIRANTIS_CLI_MSR_PLUGIN_ID,
    interfaces=[METTA_PLUGIN_INTERFACE_ROLE_CLI],
)
def metta_terraform_factory_cli_msr(environment: Environment, instance_id: str = ""):
    """Create an MSR cli plugin."""
    return MSRAPICliPlugin(environment, instance_id)


# ----- METTA bootstraps that we will use on config objects -----


def bootstrap_common(environment: Environment):
    """Metta configerus bootstrap.

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
    """Metta configerus bootstrap.

    Add some Mirantis specific config options for presets

    Additional config sources may be added based on config.load("metta")
    which will try to add config for metta `presets`
    This gives access to "variation", "cluster", "platform" and "release"
    presets.  You can dig deeper, but it might implicitly make sense if you look
    at the config folder of this module.

    @see .presets.add_preset_config() for details

    """
    add_preset_config(environment)
