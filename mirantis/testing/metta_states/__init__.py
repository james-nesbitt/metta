"""

Common METTA plugins and functionality.

Package for common shared Metta plugins that can be used by various
other plugins as a based.

"""
from typing import Dict, Any

from configerus import Config
from configerus.loaded import LOADED_KEY_ROOT

from mirantis.testing.metta.plugin import Factory
from mirantis.testing.metta.environment import Environment, METTA_PLUGIN_INTERFACE_ROLE_ENVIRONMENT
from mirantis.testing.metta_cli.base import METTA_PLUGIN_INTERFACE_ROLE_CLI

from .state_environment import (
    StateBasedEnvironment,
    METTA_ENVIRONMENT_STATE_PLUGIN_ID,
)
from .state import (
    EnvironmentStatePlugin,
    METTA_PLUGIN_INTERFACE_ROLE_ENVIRONMENTSTATE,
    METTA_STATE_DEFAULT_PLUGIN_ID,
)
from .labelactivate_state import (
    EnvironmentLabelActivateStatePlugin,
    METTA_STATE_LABELACTIVATE_PLUGIN_ID,
)


@Factory(
    plugin_id=METTA_ENVIRONMENT_STATE_PLUGIN_ID,
    interfaces=[METTA_PLUGIN_INTERFACE_ROLE_ENVIRONMENT],
)
def state_environment_factory(
    config: Config, instance_id: str, label: str = "", base: str = LOADED_KEY_ROOT
) -> StateBasedEnvironment:
    """Build a FixtureBuilderEnvironment environment."""
    return StateBasedEnvironment(config=config, instance_id=instance_id, label=label, base=base)


@Factory(
    plugin_id=METTA_STATE_DEFAULT_PLUGIN_ID,
    interfaces=[METTA_PLUGIN_INTERFACE_ROLE_ENVIRONMENTSTATE],
)
def default_environment_state_factory(
    environment: Environment, instance_id: str, label: str = "", base: str = LOADED_KEY_ROOT
) -> EnvironmentStatePlugin:
    """Build a EnvironmentState environment."""
    return EnvironmentStatePlugin(
        environment=environment, instance_id=instance_id, label=label, base=base
    )


@Factory(
    plugin_id=METTA_STATE_LABELACTIVATE_PLUGIN_ID,
    interfaces=[METTA_PLUGIN_INTERFACE_ROLE_ENVIRONMENTSTATE],
)
def labelactivate_environment_state_factory(
    environment: Environment, instance_id: str, label: str = "", base: str = LOADED_KEY_ROOT
) -> EnvironmentLabelActivateStatePlugin:
    """Build a EnvironmentState environment."""
    return EnvironmentLabelActivateStatePlugin(
        environment=environment, instance_id=instance_id, label=label, base=base
    )


# ----- METTA bootstraps that we will use on config objects -----


# pylint: disable=unused-argument
def bootstrap_bootstrapper(config: Config):
    """METTA_Terraform bootstrap.

    Currently we only use this to import plugins.

    Parameters:
    -----------
    config (Config) : an confiug which can be modified to bootstrap

    """


# pylint: disable=unused-argument
def bootstrap_environment(environment: Environment):
    """METTA_Terraform bootstrap.

    Currently we only use this to import plugins.

    Parameters:
    -----------
    env (Environment) : an environment which should have validation config added to.

    """
