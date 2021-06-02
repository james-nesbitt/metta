"""

METTA PLUGIN: Text output plugin.

An output plugin which holds a single string value as its content.

"""

import logging


logger = logging.getLogger('metta.contrib.common.output.text')

METTA_PLUGIN_ID_OUTPUT_TEXT = 'text'
""" output plugin_id for the text plugin """


class TextOutputPlugin:
    """Metta Output plugin a text output type.

    this just gets and sets text. Nothing fancy.

    """

    def __init__(self, environment, instance_id, text: str = ''):
        """Run the super constructor but also set class properties.

        Parameters:
        -----------
        data (str) : any string data to be stored

        Raises:
        -------
        A configerus.validate.ValidationError is raised if you passed in a
        validator target and validation failed.

        An AssertionError is raised if you didn't pass in a Dict.

        """
        self.environment = environment
        """ Environemnt in which this plugin exists """
        self.instance_id = instance_id
        """ Unique id for this plugin instance """

        self.set_text(text)

    def set_text(self, data: str):
        """Overwrite the contents of the output string."""
        self.text = data

    def get_output(self) -> str:
        """Retrieve assigned output string.

        Returns:
        --------
        The string that was assigned using .arguments() or set_text()

        Raises:
        -------
        AttributeError if you tried to get text before you have assigned it.

        """
        return self.text

    def info(self):
        """Return dict data about this plugin for introspection."""
        return {
            'output': {
                'text': self.text
            }
        }
