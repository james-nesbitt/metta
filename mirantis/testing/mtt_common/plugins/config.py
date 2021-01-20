
import re
import os.path
import json
import yaml
from typing import List, Dict, Any

from ...mtt.config import MTTPluginConfigSource, Config, MTT_CONFIG_PATH_LABEL

class ConfigSourceDictPlugin(MTTPluginConfigSource):
    """ Config source based on a pass dict """

    def __init__(self, config: Config, instance_id: str):
        """
        Parameters:
        -----------

        The first two arguments we don't really need, but we include as we want
        to implement the expected plugin interface

        config (Config) : all plugins receive a config object

        id (str) : instance id for the plugin.

        Now we have arguments that we actually use

        data (Dict[str, Any]) : data which will be scanned for config values

        """
        super(MTTPluginConfigSource, self).__init__(config, instance_id)

        self.data = {}
        """ keep the data that we will use for searching """

    def set_data(self, data: Dict[str,Any]):
        """ Assign Dict data to this config source plugin """
        self.data = data

    def load(self, label: str):
        """ Load a config label and return a Dict[str, Any] of config data

        Parameters:

        label (str) : label to load

        """
        if label in self.data:
            return self.data[label]
        else:
            return {}

# FileTypes that this class can use at this time
FILESOURCE_FILETYPES = [ "json", "yaml", "yml" ]
""" Valid config types that the config loader can currently handled """

class ConfigSourcePathPlugin(MTTPluginConfigSource):
    """

    Config source loader that loads files from a path

    .load(key) looks for any files in the path that are named key, with an
    extension that we know how to unmarshall (json, yml)

    """

    def __init__(self, config: Config, instance_id: str):
        """
        Parameters:
        -----------

        config (Config) : all plugins receive a config object

        id (str) : instance id for the plugin. This COnfigSource plugin uses the
           instance_id for adding the option for string substitution for the path
           if this is not empty

        """
        super(MTTPluginConfigSource, self).__init__(config, instance_id)

        self.path = ''

    def set_path(self, path: str):
        """ Set the config path source """
        self.path = path

    def load(self, label: str):
        """ load config for a name

        Parameters:
        -----------

        lable (str) : config label to load, should correlated to a json or yaml
            file of the same name in the path, otherwise an empty Dict is
            returned.

            **There is 1 special case, where if MTT_CONFIG_PATH_LABEL is passed
              then the function returns a Dict of 'instance_id:path' which can
              be used for string substitution**

        Returns:
        --------

        Dict[str, Any] of data that was loaded for the label
        """

        if not os.path.isdir(self.path):
            raise ValueError("Could not load '{}' path config, as the source path does not exist: {}".format(self.instance_id, self.path))

        # Special case for retreiving paths instead of config
        if label == MTT_CONFIG_PATH_LABEL:
            return {self.instance_id: self.path}

        data = {}
        """ hold all merged data from found source files """

        file_types_re = "|".join(FILESOURCE_FILETYPES)
        """ regex part for allowed file extensions """
        config_files_re = rf"({label})\.({file_types_re})"
        """ regex that matches all valid config filenames for the label """

        for file in [f for f in os.listdir(self.path) if re.match(config_files_re, f)]:
            with open(os.path.join(self.path, file)) as matching_file:
                extension = os.path.splitext(file)[1].lower()
                if extension == ".json":
                    try:
                        file_config = json.load(matching_file)
                    except json.decoder.JSONDecodeError as e:
                        raise ValueError("Failed to parse one of the config files '{}': {}".format(os.path.join(self.path, file), e))

                    assert file_config, "Empty config in {} from file {}".format(path, file)
                    data = self.tree_merge(file_config, data)
                elif extension == ".yml" or extension == ".yaml":
                    try:
                        file_config = yaml.load(matching_file, Loader=yaml.FullLoader)
                    except yaml.YAMLError as e:
                        raise ValueError("Failed to parse one of the config files '{}': {}".format(os.path.join(self.path, file), e))

                    assert file_config, "Empty config in {} [{}]".format(file, self.path)
                    data = self.tree_merge(file_config, data)

                else:
                    raise ValueError("Unknown config filetype. Cannot parse '{}' files, but it matches our regex".format(extension))

        return data
