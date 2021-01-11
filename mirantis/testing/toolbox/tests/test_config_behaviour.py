"""
test_config

Unit and functional testing for the config handler

"""
import json
import yaml
import os
import pytest
import logging

# Relative import so tat we can test in place
from ... import toolbox as toolbox
from ..config_sources import SourceList

logger = logging.getLogger("test_config_behaviour")
logger.setLevel(logging.INFO)

config_sources = [
    {
        "name": "first",
        "priority": 30,
        "type": "dict",
        "data": {
            "config": {
                "1": "first 1"
            },
            "variables": {
                "one": "first one",
                "two": "first two"
            }
        }
    },
    {
        "name": "second",
        "priority": 20,
        "type": "path",
        "data": {
            "config.json": {
                "1": "second 1",
                "2": "second 2"
            },
            "variables.json": {
                "one": "second one",
                "two": "second two"
            }
        }
    },
    {
        "name": "third",
        "priority": 40,
        "type": "path",
        "data": {
            "config.yaml": {
                "3": {
                    "1": "third 3.1"
                },
                "4": {
                    "1": "third 4.1"
                },
                "5": "third 5"
            }
        }
    },
    {
        "name": "fourth",
        "priority": 75,
        "type": "path",
        "data": {
            "config.json": {
                "4": "fourth 4"
            }
        }
    },
    {
        "name": "fifth",
        "priority": 75,
        "type": "path",
        "data": {
            "config.json": {
                "5": "fifth 5",
                "6": "fifth 6"
            }
        }
    },
    {
        "name": "sixth",
        "priority": 75,
        "type": "path",
        "data": {
            "config.json": {
                "6": {
                    "1": "sixth 6.1"
                }
            }
        }
    },
    {
        "name": "seventh",
        "priority": 85,
        "type": "path",
        "data": {
            "config.json": {
                "5": "seventh 5 json",
                "6": "seventh 6 json"
            },
            "config.yaml": {
                "5": "seventh 5 yaml",
                "6": "seventh 6 yaml"
            }
        }
    },
    {
        "name": "eighth",
        "priority": 80,
        "type": "dict",
        "data": {
            "config": {
                "7": "{1}",
                "8": "{variables:one}",
                "9": "{does.not.exist?default}",
                "10": "{does.not.exist}",
                "11": "{variables:does.not.exist?megadefault}",
                "12": "{variables:three?default}",
                "13": "{_source_:fifth}",
                "14": "{12}"
            },
            "variables": {
                "three": "eight three"
            }
        }
    }
]
""" Contents of test config files used as the source for a config object """


@pytest.fixture()
def sources(tmp_path):
    """ Build the source list from the config """
    # write all of the config to some temp files so that we have conf to test
    sources = toolbox.new_sources()

    logger.info("Building source list")

    for source in config_sources:
        name = source["name"]
        priority = source["priority"]
        type = source["type"]
        data = source["data"]

        if type == "dict":
            logger.info("Adding 'dict' source '%s' [%s]: %s", name, priority, data.keys())
            sources.add_dict_source(data, key=name, priority=priority)
        elif source["type"] == "path":
            # first make files for all of the data
            path = name
            full_path = os.path.join(tmp_path, path)
            os.makedirs(full_path)
            for file_name, file_data in data.items():
                full_file = os.path.join(full_path, file_name)
                logger.debug("path source '%s' writing file '%s' : %s", name, full_file, file_data)
                with open(full_file, 'w') as config_file_pointer:
                    extension = os.path.splitext(file_name)[1].lower()
                    if extension == ".json":
                        json.dump(file_data, config_file_pointer)
                    elif extension == ".yaml" or extension == ".yml":
                        yaml.dump(file_data, config_file_pointer)

            logger.info("Adding 'path' source '%s' [%s]: %s : %s", name, priority, path, data.keys())
            sources.add_filepath_source(full_path, name, priority)

    return sources

@pytest.fixture()
def config(sources):
    """ make a Config test object from some inline data

    First this dumps the data into json files, and then points the config object
    to the various paths for loading. The data can then be used to test funct.
    The data contains only values that are usefull for confirming that config
    behaviour is as expected, and is not meant to be useful.
    """

    assert isinstance(sources, SourceList), "Passed SourceList is not valid : {}".format(sources)
    return toolbox.config_from_source_list(sources=sources, include_default_config_paths=False)


@pytest.fixture()
def loaded_config(config):
    """LoadedConfig object loaded from the test config using the 'config' key"""

    return config.load("config")

@pytest.fixture()
def loaded_variables(config):
    """LoadedConfig object loaded from the test config using the 'variables' key"""

    return config.load("variables")

""" TESTS """

def test_sourcelist(tmp_path, sources):
    """ test the sourcelist behaviour """

    assert isinstance(sources, SourceList), "Invalid SourceList"

    ordered_sources = [(element.key, element.priority, element.handler.name()) for element in sources.get_ordered_sources()]

    assert len(ordered_sources) == len(config_sources)

    assert ordered_sources[0][0] == 'seventh'
    assert ordered_sources[0][1] ==  85
    assert ordered_sources[0][2] == os.path.join(tmp_path, 'seventh')
    assert ordered_sources[1][0] == 'eighth'
    assert ordered_sources[1][1] ==  80
    assert ordered_sources[1][2] == 'eighth'
    assert ordered_sources[2][0] == 'sixth'
    assert ordered_sources[2][1] ==  75
    assert ordered_sources[2][2] == os.path.join(tmp_path, 'sixth')
    assert ordered_sources[3][0] == 'fifth'
    assert ordered_sources[3][1] ==  75
    assert ordered_sources[3][2] == os.path.join(tmp_path, 'fifth')
    assert ordered_sources[4][0] == 'fourth'
    assert ordered_sources[4][1] ==  75
    assert ordered_sources[4][2] == os.path.join(tmp_path, 'fourth')
    assert ordered_sources[5][0] == 'third'
    assert ordered_sources[5][1] ==  40
    assert ordered_sources[5][2] == os.path.join(tmp_path, 'third')
    assert ordered_sources[6][0] == 'first'
    assert ordered_sources[6][1] ==  30
    assert ordered_sources[6][2] == 'first'
    assert ordered_sources[7][0] == 'second'
    assert ordered_sources[7][1] ==  20
    assert ordered_sources[7][2] == os.path.join(tmp_path, 'second')

def test_dict_source(sources):
    """ basic dict source handler testing """

    first = sources.source("first")
    first_variables = first.handler.load("variables")

    assert first_variables.get("one") == "first one"

def test_basic_combined(loaded_config):
    """ test some basic file combining by the config object """

    assert loaded_config.get("1") == "first 1"
    assert loaded_config.get("2") == "second 2"

def test_dot_notation(loaded_config):
    """ Confirm that we can retrieve data using the dot notation """

    assert loaded_config.get("3.1") == "third 3.1"

def test_overrides(loaded_config):
    """ confirm that keys defined in more than one source get overriden """

    assert loaded_config.get("4") == "fourth 4"
    assert loaded_config.get("5.1", exception_if_missing=False) == None
    assert loaded_config.get("5") == "seventh 5 json"

def test_config_format(loaded_config, loaded_variables):
    """ test the direct string format options """

    assert loaded_config.format_string("{1}") == loaded_config.get("1")
    # test basic string substitution"
    assert loaded_config.format_string("{variables:three}") == loaded_variables.get("three")
    # test cross sources string formatting
    assert loaded_config.format_string("{variables:three?default}") == loaded_config.get("12")
    # test additional config takes precedence over config

def test_variable_templating(loaded_config, loaded_variables):
    """ confirm that values can contain template references to other values """

    assert loaded_config.get("7") == loaded_config.get("1")
    # test replacement from the same label/source

    assert loaded_config.get("8") == loaded_variables.get("one")
    # test replacement from a different source

    assert loaded_config.get("9") == "default"
    # test formatting default values

    #assert loaded_config.get("10", strip_missing=True) == ""
    # test strip missing values - NO LONGER AN OPTION

    assert loaded_config.get("11") == "megadefault"
    # test a bunch of things tofether

    assert loaded_config.get("12") == loaded_variables.get("three")
    # test that default doesn't swap a positive search
