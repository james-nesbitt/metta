"""

Metta Mirantis.

Common components and configuration which are nice to use
when using metta with Mirantis products.

THese are entirely optional, but it makes a lot of
operations easier.

"""

from typing import List, Dict

from configerus.loaded import LOADED_KEY_ROOT

from mirantis.testing.metta.plugin import Factory
from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.provisioner import METTA_PLUGIN_INTERFACE_ROLE_PROVISIONER


from .mke_provisioner import (
    MKEProvisionerPlugin,
    METTA_MIRANTIS_PROVISIONER_MKE_PLUGIN_ID,
    METTA_MIRANTIS_MKE_CONFIG_LABEL,
)
from .msr_client import (
    MSRProvisionerPlugin,
    METTA_MIRANTIS_PROVISIONER_MSR_PLUGIN_ID,
    METTA_MIRANTIS_MSR_CONFIG_LABEL,
)

# ----- Plugin factories -----


@Factory(
    plugin_id=METTA_MIRANTIS_PROVISIONER_MKE_PLUGIN_ID,
    interfaces=[METTA_PLUGIN_INTERFACE_ROLE_PROVISIONER],
)
def metta_terraform_factory_provisioner_mke(
    environment: Environment,
    instance_id: str,
    label: str = METTA_MIRANTIS_MKE_CONFIG_LABEL,
    base: str = LOADED_KEY_ROOT,
) -> MKEProvisionerPlugin:
    """Create an MKE provisioner plugin."""
    return MKEProvisionerPlugin(
        environment=environment, instance_id=instance_id, label=label, base=base
    )


@Factory(
    plugin_id=METTA_MIRANTIS_PROVISIONER_MSR_PLUGIN_ID,
    interfaces=[METTA_PLUGIN_INTERFACE_ROLE_PROVISIONER],
)
def metta_terraform_factory_provisioner_msr(
    environment: Environment,
    instance_id: str,
    label: str = METTA_MIRANTIS_MSR_CONFIG_LABEL,
    base: str = LOADED_KEY_ROOT,
) -> MSRProvisionerPlugin:
    """Create an MSR provisioner plugin."""
    return MSRProvisionerPlugin(
        environment=environment, instance_id=instance_id, label=label, base=base
    )


# ----- SetupTools EntryPoint METTA BootStrapping -----


# pylint: disable=unused-argument
def bootstrap(environment: Environment):
    """Metta configerus bootstrap.

    Add some Mirantis specific config options for presets

    """
