"""

Metta CLI : Config commands.

Various commands that allow introspection of the configerus config setup and
values.  There are commands for inspecting which plugins are avaialble, and
what configuration sources are setup, but also for examining rendered config
and formatting strings using config - all to allow verification of what
config is feeding metta.

"""
import logging

from configerus.loaded import LOADED_KEY_ROOT
from configerus.plugin import Type as ConfigerusType
from configerus.contrib.files import PLUGIN_ID_SOURCE_PATH
from configerus.contrib.dict import PLUGIN_ID_SOURCE_DICT

from mirantis.testing.metta.environment import Environment

from .base import CliBase, cli_output

logger = logging.getLogger("metta.cli.config")


# this interface is common for all Metta plugins, but CLI plugins underuse it
# pylint: disable=too-few-public-methods
class ConfigCliPlugin(CliBase):
    """Fire command/group generator for config commands."""

    def fire(self):
        """Return a dict of commands."""
        return {"config": ConfigGroup(self._environment)}


class ConfigGroup:
    """Base Fire command group for output commands."""

    def __init__(self, environment: Environment):
        """Store environment in object."""
        self._environment: Environment = environment

    def plugins(self, plugin_id: str = "", instance_id: str = "", plugin_type: str = ""):
        """List configerus plugins."""
        configerus_plugin_list = []
        for instance in self._environment.config().plugins.get_instances(
            plugin_id=plugin_id, instance_id=instance_id, type=plugin_type
        ):
            configerus_plugin_list.append(
                {
                    "type": instance.type,
                    "plugin_id": instance.plugin_id,
                    "instance_id": instance.instance_id,
                    "priority": instance.priority,
                }
            )
        return cli_output(configerus_plugin_list)

    def sources(self, plugin_id: str = "", instance_id: str = "", deep: bool = False):
        """List configerus sources."""
        source_list = []
        for instance in self._environment.config().plugins.get_instances(
            plugin_id=plugin_id, instance_id=instance_id, type=ConfigerusType.SOURCE
        ):
            source = {
                "plugin_id": instance.plugin_id,
                "instance_id": instance.instance_id,
                "priority": instance.priority,
            }

            if deep:
                if instance.plugin_id == PLUGIN_ID_SOURCE_PATH:
                    source["path"] = instance.plugin.path
                if instance.plugin_id == PLUGIN_ID_SOURCE_DICT:
                    source["data"] = instance.plugin.data

            source_list.append(source)

        return cli_output(source_list)

    def loaded(self, raw: bool = False):
        """List loaded config labels."""
        loaded = self._environment.config().loaded
        value = list(loaded)
        if raw:
            return value
        return cli_output(value)

    def get(self, label: str, key: str = LOADED_KEY_ROOT):
        """Retrieve configuration from the config object.

        USAGE:

            metta config get {label} [{key}]

        """
        try:
            loaded = self._environment.config().load(label)
        except KeyError:
            return f"Could not find the config label '{label}'"

        try:
            value = loaded.get(key)
        except KeyError:
            return f"Could not find the config key '{key}'"

        return cli_output(value)

    # broad exception catch just to format error message
    # pylint: disable=broad-except
    def format(self, data: str, default_label: str = None, raw: bool = False):
        """Format a target string using config templating."""
        try:
            if default_label is None:
                default_label = "you did not specify a default"
            value = self._environment.config().format(data=data, default_label=default_label)
        except Exception as err:
            return f"Error occured in formatting: '{err}'"

        if raw:
            return value
        return cli_output(value)
