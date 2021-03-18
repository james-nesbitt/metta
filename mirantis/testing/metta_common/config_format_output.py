
import re
import logging

from configerus.config import Config

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.plugin import Type
from mirantis.testing.metta_common.dict_output import DictOutputPlugin
from mirantis.testing.metta_common.text_output import TextOutputPlugin

OUTPUT_FORMAT_MATCH_PATTERN = r'(?P<output>(\w+)+)(\/(?P<base>[\-\.\w]+))?'
""" A regex pattern to identify outputs that should be embedded """

logger = logging.getLogger('configerus.contrib.files:output')


class ConfigFormatOutputPlugin:
    """   """

    def __init__(self, config: Config, instance_id: str):
        """  """
        self.config = config
        self.instance_id = instance_id

        self.pattern = re.compile(OUTPUT_FORMAT_MATCH_PATTERN)
        """ Regex patter for identifying an output replacement """

        self.environment = None
        """ environment which contains the outputs. Must be added """

    def set_environemnt(self, environment: Environment):
        """ set the output environment

        @NOTE this is obligatory

        """
        self.environment = environment

    def format(self, key, default_label: str):
        """ Format a string by substituting config values

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
            raise KeyError(
                "Could not interpret Format action key '{}'".format(key))

        output = match.group('output')

        try:
            output = self.environment.fixtures.get_plugin(
                type=Type.OUTPUT, instance_id=output)

            if isinstance(output, DictOutputPlugin):
                base = match.group('base')
                if base is not None:
                    return output.get_output(base)
                return output.get_output()
            elif isinstance(output, TextOutputPlugin):
                return output.get_output()
            elif hasattr(output, 'get_output'):
                return output.get_output()

        except KeyError as e:
            raise KeyError(
                "Config replace for output failed as output '{}' was not found, and no default value was suggested.".format(output)) from e
