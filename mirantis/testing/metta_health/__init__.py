"""

Common METTA plugins and functionality.

Package for common shared Metta plugins that can be used by various
other plugins as a based.

"""
from typing import Any
from configerus.loaded import LOADED_KEY_ROOT

from mirantis.testing.metta.plugin import Factory
from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.client import METTA_PLUGIN_INTERFACE_ROLE_CLIENT
from mirantis.testing.metta.workload import METTA_PLUGIN_INTERFACE_ROLE_WORKLOAD
from mirantis.testing.metta.output import METTA_PLUGIN_INTERFACE_ROLE_OUTPUT

from mirantis.testing.metta_cli.base import METTA_PLUGIN_INTERFACE_ROLE_CLI

from .health_client import HealthClientPlugin, METTA_HEALTH_CLIENT_PLUGIN_ID
from .healthpoll_workload import (
    HealthPollWorkload,
    METTA_PLUGIN_ID_WORKLOAD_HEALTHPOLL,
    HEALTHPOLL_CONFIG_LABEL,
)
from .cli import HealthCliPlugin, METTA_PLUGIN_ID_HEALTH_CLI


@Factory(
    plugin_id=METTA_HEALTH_CLIENT_PLUGIN_ID,
    interfaces=[METTA_PLUGIN_INTERFACE_ROLE_CLIENT],
)
def metta_plugin_factory_client_health(environment: Environment, instance_id: str = ""):
    """Create an metta health client plugin."""
    return HealthClientPlugin(environment, instance_id)


@Factory(
    plugin_id=METTA_PLUGIN_ID_WORKLOAD_HEALTHPOLL,
    interfaces=[METTA_PLUGIN_INTERFACE_ROLE_WORKLOAD],
)
def metta_plugin_factory_workload_healthpoll(
    environment: Environment,
    instance_id: str = "",
    label: str = HEALTHPOLL_CONFIG_LABEL,
    base: Any = LOADED_KEY_ROOT,
):
    """Create an metta health polling workload plugin."""
    return HealthPollWorkload(environment, instance_id, label=label, base=base)


@Factory(
    plugin_id=METTA_PLUGIN_ID_HEALTH_CLI,
    interfaces=[METTA_PLUGIN_INTERFACE_ROLE_CLI],
)
def metta_plugin_factory_cli_health(environment: Environment, instance_id: str = ""):
    """Create an healthpoll cli plugin."""
    return HealthCliPlugin(environment, instance_id)


# ----- METTA bootstraps that we will use on config objects -----


METTA_HEALTH_ALLHEALTH_INSTANCE_ID = "all-health"
"""Metta ficture intance-id for a health client that will be added to the env."""

# pylint: disable=unused-argument
def bootstrap_environment(environment: Environment):
    """METTA_Health bootstrap.

    Use this to create a generic health client in any environment passed

    Parameters:
    -----------
    env (Environment) : an environment which should a client added

    """
    environment.add_fixture_from_dict(
        plugin_dict={
            "plugin_id": METTA_HEALTH_CLIENT_PLUGIN_ID,
            "priority": 50,
            "instance_id": METTA_HEALTH_ALLHEALTH_INSTANCE_ID,
            "labels": {
                "source": "metta_health::bootstrap",
                "container": "environment",
                "container_id": environment.instance_id(),
            },
            "arguments": {},
        }
    )
