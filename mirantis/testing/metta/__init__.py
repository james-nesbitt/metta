"""

Metta - A testing system management framework.

In this module, the root package, are found a number of tool plugin constructors
that can be used to get instances of the plugins based on either passed in data
or configerus config.

The contstruction.py module does the heavy lifting of building plugins and
PluginInstances sets.

"""
import os
from typing import List, Callable, Dict, Any
import logging

from configerus.config import Config

from .plugin import Factory
from .config import default_config

# this also registers the core bootstrap plugins
from .bootstrap import METTA_BOOTSTRAPPER_PROJECT_PLUGIN_ID as DEFAULT_BOOTSTRAPPER
from .fixture import Fixture

# This also registers the core environment plugins
from .environment import (
    Environment,
    METTA_BUILDER_ENVIRONMENT_PLUGIN_ID as DEFAULT_ENVIRONMENT,
    METTA_PLUGIN_INTERFACE_ROLE_ENVIRONMENT,
)
from .globals import global_fixtures

logger = logging.getLogger("metta")

""" METTA and Configerus bootstrapping """

FIXED_CONFIGERUS_BOOSTRAPS = ["get", "env", "jsonschema", "dict", "files"]
""" configerus bootstraps that we will use on config objects. We use functionality
    in the core which heavily depends on this config, so it is necessary """


def discover(
    boostrapper_plugin_id: str = DEFAULT_BOOTSTRAPPER,
    config: Config = None,
    labels: Dict[str, str] = None,
    arguments: Dict[str, Any] = None,
) -> Fixture:
    """Ask Metta to discover and generate everything from config.

    Do you prefer to just write some config, and then have Metta do all of the
    preparation for you?

    You can optionally provide some of the components, but if you don't Metta
    will create what it needs on the fly.

    Parameters:
    -----------

    bootrapper (str) : Bootstrapper plugin id for the function which should be
        used to bootstrap this metta session.

    config (Config) : optionally provide a configerus Config object in if you
        want to provide prepopulated config.
        This method will make one if needed.

    """
    if config is None:
        config = default_config(FIXED_CONFIGERUS_BOOSTRAPS)

    instance_id = "bootstrapper"
    args: List[Any] = [config, instance_id]
    kwargs: Dict[str, Any] = arguments if arguments is not None else {}
    plugin_instance = Factory.create(boostrapper_plugin_id, instance_id, *args, **kwargs)

    # Build a fixture from the plugin_instance and add it to the fixtures
    # set for the environment, then return the fixture.
    fixture = global_fixtures.add(
        fixture=Fixture.from_instance(
            plugin_instance, priority=95, labels=labels if labels is not None else {}
        ),
        replace_existing=True,
    )
    return fixture


# pylint: disable=too-many-arguments
# This is what it takes to build a plugin.
def new_environment(
    name: str,
    config: Config = None,
    environment_plugin_id: str = DEFAULT_ENVIRONMENT,
    priority: int = 70,
    replace_existing: bool = False,
    labels: Dict[str, str] = None,
    arguments: Dict[str, Any] = None,
) -> Fixture:
    """Environment only way to use Metta.

    Not only do you not want to know about Spaces, but you actually don't want
    all of that, and can manage your own business.  Use this and get just an
    Environment object.

    You can optionally provide some of the components, but if you don't Metta
    will create what it needs on the fly.

    """
    if config is None:
        config = default_config(FIXED_CONFIGERUS_BOOSTRAPS)

    instance_id = name
    args: List[Any] = [config, instance_id]
    kwargs: Dict[str, Any] = arguments if arguments is not None else {}
    plugin_instance = Factory.create(environment_plugin_id, instance_id, *args, **kwargs)

    # Build a fixture from the plugin_instance and add it to the fixtures
    # set for the environment, then return the fixture.
    fixture = global_fixtures.add(
        fixture=Fixture.from_instance(
            plugin_instance, priority=priority, labels=labels if labels is not None else {}
        ),
        replace_existing=replace_existing,
    )
    return fixture


def environment_names() -> List[str]:
    """List all of the environment names that have been created."""
    return list(
        fixture.instance_id
        for fixture in global_fixtures.filter(interfaces=[METTA_PLUGIN_INTERFACE_ROLE_ENVIRONMENT])
    )


def get_environment(name: str = None) -> Environment:
    """Retrieve an environment.

    If no environment name is passed then the highest priority environment is returned.
    """
    return global_fixtures.get_plugin(
        instance_id=name, interfaces=[METTA_PLUGIN_INTERFACE_ROLE_ENVIRONMENT]
    )


def new_plugin(plugin_id: str, instance_id: str, *args, **kwargs):
    """Generate a plugin with your own values.

    Are you so on top of it that you just want to use the plugin registration
    and creation part of Metta.  With this method you are welcome to take
    advantage of the plugin system, but are expected to handle everything
    yourself.

    It is up to the consumer to make sure that any desired plugins are already
    registered, which can usually be done by simply importing the python modules
    that container the decorated factory functions.

    """
    priority = 75
    labels: Dict[str, str] = {"parent": "global"}
    plugin_instance = Factory.create(plugin_id, instance_id, *args, **kwargs)
    fixture = global_fixtures.add(
        fixture=Fixture.from_instance(plugin_instance, priority=priority, labels=labels),
        replace_existing=True,
    )
    return fixture.plugin
