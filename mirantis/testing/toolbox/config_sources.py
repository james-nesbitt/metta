"""

Path handling and sorting

"""

import re
import os.path
import json
import yaml
from typing import List, Dict, Any
from .tools import _tree_merge


CONFIG_SOURCE_DEFAULT_PRIORITY = 75


class SourceList:
    """ An orderd list of paths """

    def __init__(self, sources: List["Source"] = []):
        """ just make sure we got parameters we need """

        self.sources = {}
        """ all of the created paths by key """

        for source in sources:
            self.add_source_object(source)

    def add_filepath_source(self, path: str, key: str="", priority: int=CONFIG_SOURCE_DEFAULT_PRIORITY):
        """ Add a path source """
        source = Source(ConfigSourceFileHandler(path), key, priority)
        self.add_source_object(source)

    def add_dict_source(self, data: Dict[str, Any], key: str="", priority: int=CONFIG_SOURCE_DEFAULT_PRIORITY):
        """ Add a dict source.  Top level of the dict must be source labels, children are config data """
        source = Source(ConfigSourceFixedSet(data, key), key, priority)
        self.add_source_object(source)

    def add_source_object(self, source: "Source"):
        """ add a source object """
        assert isinstance(source, Source), "Non source passed to add source object"
        self.sources[source.key] = source

    def source_names(self) -> List[str]:
        """ Get a list of the source names """
        names = []
        for source in self.sources.values():
            names.append(source.key)
        return names

    def source(self, name:str):
        """ Get source object for a key """
        return self.sources[name]

    def get_ordered_sources(self):
        """ retieve a flat ordered List of str paths """

        ordered = {}
        for source in self.sources.values():
            assert isinstance(source, Source), "How did a non-source get in here: {}".format(source)
            priority = source.priority
            if not priority in ordered:
                ordered[priority] = []

            ordered[priority].append(source)

        all = []
        for prioritygroup in sorted(ordered.keys()):
            for source in ordered[prioritygroup]:
                all.append(source)

        all.reverse()
        return all

class Source:
    """ Path struct """

    def __init__(self, handler, key: str = "", priority: int = 75):
        """
        Parameters:

        path (str): path to be used
        key (str): key name for the path
        priority (int): int priority with larger being higher

        """

        self.handler = handler
        self.key = key
        self.priority = priority


""" Config sources """

class ConfigSourceFixedSet:
    """

    Config source loaded from a passed Dict tree

    The top level of the tree represents `label`s that can be loaded, and the
    children nodes are considered the label config

    The purpose is to allow an interface for oinjecting config data calculated
    in run time, as opposed to being pulled from a source

    """

    def __init__(self, data: Dict[str, Any], name: str=""):
        """

        data (Dict[str, Any]): source data used for load calls

        name (str) : optional name used for template substitution calls

        """
        self.data = data
        self._name = name

    def name(self):
        """ return the source optional name """
        return self._name

    def load(self, label: str):
        """ load config for a name
        Parameters:

        label (str) : config label to load, top level of the passed data

        returns:

        Dict[str, Any], emtpty if label was not found

        """
        if label in self.data:
            return self.data[label]
        else:
            return {}

# FileTypes that this class can use at this time
FILESOURCE_FILETYPES = [ "json", "yaml", "yml" ]
""" Valid config types that the config loader can currently handled """

class ConfigSourceFileHandler:
    """

    Config source loader that loads files from a path

    """

    def __init__(self, path: str):
        """ string path for where files could be """
        self.path = path

    def name(self):
        """ return the source path as a name """
        return self.path

    def load(self, label: str):
        """ load config for a name

        returns:

        Dict[str, Any]
        """

        file_types_re = "|".join(FILESOURCE_FILETYPES)
        """ regex part for allowed file extensions """

        data = {}
        """ hold all merged data from found sources """

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
                    data = _tree_merge(file_config, data)
                elif extension == ".yml" or extension == ".yaml":
                    try:
                        file_config = yaml.load(matching_file, Loader=yaml.FullLoader)
                    except ImportError as e:
                        raise ValueError("Failed to parse one of the config files '{}': {}".format(os.path.join(self.path, file), e))

                    assert file_config, "Empty config in {} from file {}".format(self.path, file)
                    data = _tree_merge(file_config, data)

                else:
                    raise ValueError("Unknown config filetype. Cannot parse '{}' files, but it matches our regex".format(extension))

        return data
