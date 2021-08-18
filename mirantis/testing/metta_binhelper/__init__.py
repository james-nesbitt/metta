"""

Common METTA plugins and functionality.

Package for common shared Metta plugins that can be used by various
other plugins as a based.

"""
from typing import Dict, Any

from configerus.loaded import LOADED_KEY_ROOT

from mirantis.testing.metta.plugin import Factory
from mirantis.testing.metta.environment import Environment


from .binhelper_utility import (
    DownloadableExecutableUtility,
    METTA_PLUGIN_ID_UTILITY_BINHELPER,
    BINHELPER_UTILITY_CONFIG_LABEL,
)


METTA_PLUGIN_INTERFACE_ROLE_UTILITY = "utility"
""" metta pluging_type for utility plugins """


@Factory(
    plugin_id=METTA_PLUGIN_ID_UTILITY_BINHELPER,
    interfaces=[METTA_PLUGIN_INTERFACE_ROLE_UTILITY],
)
def metta_plugin_factory_utility_binhelper(
    environment: Environment,
    instance_id: str,
    label: str = BINHELPER_UTILITY_CONFIG_LABEL,
    base: Any = LOADED_KEY_ROOT,
):
    """Create a bin-helper utility plugin."""
    return DownloadableExecutableUtility(environment, instance_id, label=label, base=base)


# ----- METTA bootstraps that we will use on config objects -----


# pylint: disable=unused-argument
def bootstrap_environment(environment: Environment):
    """METTA_Terraform bootstrap.

    Currently we only use this to import plugins.

    Parameters:
    -----------
    env (Environment) : an environment which should have validation config added to.

    """
