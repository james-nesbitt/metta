import logging
from typing import Dict

from configerus.loaded import Loaded, LOADED_KEY_ROOT
from mirantis.testing.metta.output import OutputBase

logger = logging.getLogger('metta.contrib.common.output.dict')


class DictOutputPlugin(OutputBase):
    """ metta Output plugin a Dict output type

    This output plugin leverages configurators features, treating the dict as
    a config source, in order to get validation and navigations.

    """

    def __init__(self, environment, instance_id,
                 data: Dict = {}, validator: str = ''):
        """ Run the super constructor but also set class properties

        Here we treat the data dict as a configerus.loaded.Loaded instance,
        with out config as a parent, so that we can leverage the configerus
        tools for searching, formating and validation.

        a configerus.loaded.Loaded object is kept for the config.

        Parameters:
        -----------

        data (Dict) : any dict data to be stored

        validator (str) : a configerus validator target if you want valdiation
            applied to the data before it is added.

        Raises:
        -------

        A configerus.validate.ValidationError is raised if you passed in a
        validator target and validation failed.

        An AssertionError is raised if you didn't pass in a Dict.

        """
        super(OutputBase, self).__init__(environment, instance_id)

        self.set_data(data, validator)

    def set_data(self, data: Dict = {}, validator: str = ''):
        """ Re-set the data for the output """
        assert isinstance(
            data, dict), "Expected Dict of data, got {}".format(data)

        if validator:
            self.environment.config.validate(data, validator)

        mock_instance_id = 'dict-output-{}'.format(self.instance_id)
        self.loaded = Loaded(
            data=data,
            parent=self.environment.config,
            instance_id=mock_instance_id)

    def get_output(self, key: str = LOADED_KEY_ROOT, validator: str = ''):
        """ retrieve an output

        Because we treated that data as a high-priority configerus source with
        a custom label, we can retrieve data from that source easily and also
        leverage other configerus options such as templating and validation

        If you don't pass a key, you will get the entire data value

        Parameters:
        -----------

        key (str) : you can optionally pass a key to retrieve only a part of the
            data structure.  This uses the configerus .get() command which uses
            dot "." notation to descend a tree.

        validator (str) : you can tell configerus to apply a validator to the
            return value

        Returns:
        --------

        Any of retreived data in the assigned data, as though you were making
        a configerus.loaded.Loaded.get()

        Raises:
        -------

        AttributeError if you are trying to get output before you have
        assigned data using .arguments()

        configerus.validate.ValidationError if you passed in a validator and
        validation failed.

        """
        return self.loaded.get(key, validator=validator)

    def info(self):
        """ Return dict data about this plugin for introspection """
        return {
            'output': {
                'data': self.loaded.data
            }
        }
