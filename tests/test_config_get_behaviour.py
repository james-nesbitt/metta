"""
test_config

Unit and functional testing for the config handler

"""
import json
import yaml
import os
import pytest
import logging

import mirantis.testing.mtt as mtt
import mirantis.testing.mtt_common as mtt_common

logger = logging.getLogger("test_config_behaviour")
logger.setLevel(logging.DEBUG)

config_sources = [
    {
        "name": "first",
        "priority": 30,
        "type": mtt_common.MTT_PLUGIN_ID_CONFIGSOURCE_DICT,
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
        "type": mtt_common.MTT_PLUGIN_ID_CONFIGSOURCE_PATH,
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
        "type": mtt_common.MTT_PLUGIN_ID_CONFIGSOURCE_PATH,
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
        "type": mtt_common.MTT_PLUGIN_ID_CONFIGSOURCE_PATH,
        "data": {
            "config.json": {
                "4": "fourth 4"
            }
        }
    },
    {
        "name": "fifth",
        "priority": 75,
        "type": mtt_common.MTT_PLUGIN_ID_CONFIGSOURCE_PATH,
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
        "type": mtt_common.MTT_PLUGIN_ID_CONFIGSOURCE_PATH,
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
        "type": mtt_common.MTT_PLUGIN_ID_CONFIGSOURCE_PATH,
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
        "type": mtt_common.MTT_PLUGIN_ID_CONFIGSOURCE_DICT,
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
def config(tmp_path):
    """ make a Config test object from some inline data

    First this dumps the data into json files, and then points the config object
    to the various paths for loading. The data can then be used to test funct.
    The data contains only values that are usefull for confirming that config
    behaviour is as expected, and is not meant to be useful.
    """

    logger.info("Building empty config object")
    config = mtt.new_config()

    logger.info("Building source list")
    for source in config_sources:
        name = source["name"]
        priority = source["priority"] if "priority" in source else config.default_priority()
        type = source["type"]
        data = source["data"]

        if type == mtt_common.MTT_PLUGIN_ID_CONFIGSOURCE_DICT:
            logger.info("Adding 'dict' source '%s' [%s]: %s", name, priority, data.keys())
            config.add_source(type, name, priority).set_data(data)
        elif type == mtt_common.MTT_PLUGIN_ID_CONFIGSOURCE_PATH:
            # first make files for all of the data
            path = name
            full_path = os.path.join(tmp_path, path)
            os.makedirs(full_path)
            for file_name, file_data in data.items():
                full_file = os.path.join(full_path, file_name)
                logger.debug("path source '%s' writing file '%s' : %s", name, full_file, file_data)
                with open(full_file, 'w') as config_file_pointer:
                    extension = os.path.splitext(file_name)[1].lower()[1:]
                    if extension == "json":
                        json.dump(file_data, config_file_pointer)
                    elif extension == "yaml" or extension == "yml":
                        yaml.dump(file_data, config_file_pointer)

            logger.info("Adding 'path' source '%s' [%s]: %s : %s", name, priority, path, data.keys())
            config.add_source(type, name, priority).set_path(full_path)

    return config

@pytest.fixture()
def loaded_config(config):
    """LoadedConfig object loaded from the test config using the 'config' key"""
    return config.load("config")

@pytest.fixture()
def loaded_variables(config):
    """LoadedConfig object loaded from the test config using the 'variables' key"""
    return config.load("variables")

""" TESTS """

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

def test_copy_safety(config):
    """ Test that config copy allows overloads and doesn't modify the source """

    config.add_source(mtt_common.MTT_PLUGIN_ID_CONFIGSOURCE_DICT, 'orig', 80).set_data({
        'copy': {
            'one': 'orig 1'
        }
    })

    config_copy_orig = config.load('copy')

    copy1 = config.copy()
    copy1.add_source(mtt_common.MTT_PLUGIN_ID_CONFIGSOURCE_DICT, 'copy1', 80).set_data({
        'copy': {
            'one': 'copy1 1',
            'two': 'copy1 2'
        }
    })
    copy2 = config.copy()
    copy2.add_source(mtt_common.MTT_PLUGIN_ID_CONFIGSOURCE_DICT, 'copy2', 81).set_data({
        'copy': {
            'one': 'copy2 1',
            'two': 'copy2 2'
        }
    })

    config_copy_late = config.load('copy')
    config1_copy = copy1.load('copy')
    config2_copy = copy2.load('copy', force_reload=True)

    logger.info('orig: %s',config_copy_orig.data )
    logger.info('1: %s',config1_copy.data )
    logger.info('2: %s',config2_copy.data )
    logger.info('late: %s',config_copy_late.data )

    # check original values
    assert config_copy_orig.get('one') == 'orig 1'
    assert config_copy_orig.get('two') == None
    # check that copied config didn't modify original
    assert config_copy_orig.get('one') == config_copy_late.get('one')
    assert config_copy_orig.get('two') == config_copy_late.get('two')

    assert config1_copy.get('one') == 'copy1 1'
    assert config1_copy.get('two') == 'copy1 2'
