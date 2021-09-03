"""

Configerus extension to connect metta output plugins to configerus formatting.

This allows embedding of metta output content into configerus configuration.

"""
import re
import logging

from configerus.config import Config
from configerus.loaded import LOADED_KEY_ROOT

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.output import METTA_PLUGIN_INTERFACE_ROLE_OUTPUT
from mirantis.testing.metta_common.dict_output import DictOutputPlugin
from mirantis.testing.metta_common.text_output import TextOutputPlugin

logger = logging.getLogger("configerus.contrib.files:output")


OUTPUT_FORMAT_MATCH_PATTERN = r"(?P<output>(\w+)+)(\/(?P<base>[\-\.\w]+))?"
""" A regex pattern to identify outputs that should be embedded """


PLUGIN_ID_FORMAT_OUTPUT = "output"
""" Format plugin_id for the configerus output format plugin """


class ConfigFormatOutputPlugin:
    """Configerus formatter plugin that uses Metta outputs as a source."""

    def __init__(self, config: Config, instance_id: str):
        """Create configerus format plugin."""
        self.config = config
        self._instance_id: str = instance_id

        self.pattern = re.compile(OUTPUT_FORMAT_MATCH_PATTERN)
        """ Regex patter for identifying an output replacement """

        self._environment: Environment = None
        """ environment which contains the outputs. Must be added """

    def copy(self):
        """Make a copy of this plugin."""
        plugin_copy = ConfigFormatOutputPlugin(self.config, self._instance_id)
        plugin_copy.set_environment(self._environment)
        return plugin_copy

    def set_environment(self, environment: Environment):
        """Set the output environment.

        @NOTE this is obligatory

        """
        self._environment = environment

    # this method is a part of an itnerface. default label is not used by us but it will be passed
    # pylint: disable=unused-argument
    def format(self, key, default_label: str):
        """Format a string by substituting config values.

        Parameters
        ----------
        key: a string that should gies instructions to the formatter on how to
            create a format replacementsrmed

        default_source : if format/replace patterns don't have a source defined
            then this is used as a source.

        """
        # if the entire key is the match, then replace whatever type we get
        # out of the config .get() call
        match = self.pattern.fullmatch(key)
        if not match:
            raise KeyError(f"Could not interpret Format action key '{key}'")

        output = match.group("output")

        try:
            output_plugin = (
                self._environment.fixtures()
                .get(interfaces=[METTA_PLUGIN_INTERFACE_ROLE_OUTPUT], instance_id=output)
                .plugin
            )

            if isinstance(output_plugin, DictOutputPlugin):
                base = match.group("base")
                if not base:
                    base = LOADED_KEY_ROOT
                return output_plugin.get_output(base)
            if isinstance(output_plugin, TextOutputPlugin):
                return output_plugin.get_output()
            if hasattr(output_plugin, "get_output"):
                return output_plugin.get_output()

            return ""

        except KeyError as err:
            raise KeyError(
                f"Config replace for output failed as output '{output}' was not found, "
                "and no default value was suggested."
            ) from err
