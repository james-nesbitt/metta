"""
test_config

Unit and functional testing for the config handler

"""
import json
import os
import pytest

# Relative import so tat we can test in place
from ... import toolbox

additional_values = {
    "100": "one-hundred from additional",
    "6": "six from additional"
}
files_data = [
    {
        "path": "first",
        "label": "test",
        "type": "json",
        "priority": 50,
        "data": {
            "1": "one",
            "4": "four-from-one"
        }
    },
    {
        "path": "second",
        "label": "test",
        "type": "json",
        "priority": 60,
        "data": {
            "2": "two"
        }
    },
    {
        "path": "third",
        "label": "test",
        "type": "json",
        "data": {
            "3": {
                "1": "three-one"
            },
            "5": {
                "1": "five-one from three"
            }
        }
    },
    {
        "path": "fifth",
        "label": "test",
        "type": "json",
        "priority": 90,
        "data": {
            "5": {
                "1": "five-one from five"
            },
            "6" : "six from five"
        }
    },
    {
        "path": "fourth",
        "label": "test",
        "type": "json",
        "priority": 9,
        "data": {
            "4": "four-from-four",
            "5": {
                "1": "five-one from four"
            }
        }
    },
    {
        "path": "fourth",
        "label": "variables",
        "type": "json",
        "priority": 9,
        "data": {
            "first": "one from four"
        }
    },
    {
        "path": "sixth",
        "label": "variables",
        "type": "json",
        "priority": 80,
        "data": {
            "first": "one from six",
            "third": "three from six"
        }
    },
    {
        "path": "fifth",
        "label": "variables",
        "type": "json",
        "priority": 90,
        "data": {
            "first": "one from five",
            "second": "two from fiv",
            "fourth": "four from fiv"
        }
    },
    {
        "path": "seventh",
        "label": "test",
        "type": "json",
        "data": {
            "7": "{1}",
            "8": "{variables:first}",
            "9": "{does.not.exist?default}",
            "10": "{does.not.exist}",
            "11": "{variables:does.not.exist?megadefault}",
            "12": "{variables:third?default}",
            "13": "{_source_:fifth}",
            "14": "{13}"
        }
    }
]
""" Contents of test config files used as the source for a config object """


@pytest.fixture()
def sourcelist(tmp_path):
    """ Build the source list from the config """
    # write all of the config to some temp files so that we have conf to test
    sources = toolbox.new_sources()
    for file_data in files_data:
        file_data["full_path"] = os.path.join(tmp_path, file_data["path"])
        file_data["file"] = "{}.{}".format(file_data["label"], file_data["type"])
        file_data["full_file"] = os.path.join(file_data["full_path"], file_data["file"])

        file_data["isDir"] = os.path.isdir(file_data["full_path"])

        if not file_data["isDir"]:
            os.makedirs(file_data["full_path"])
            # file_data["path"] is used as the source name
            sources.add_filepath_source(file_data["full_path"], file_data["path"], file_data["priority"] if "priority" in file_data else 75)

        with open(file_data["full_file"], 'w') as config_file_pointer:
            if file_data["type"] == "json":
                json.dump(file_data["data"], config_file_pointer)

    return sources

@pytest.fixture()
def config(sourcelist):
    """ make a Config test object from some inline data

    First this dumps the data into json files, and then points the config object
    to the various paths for loading. The data can then be used to test funct.
    The data contains only values that are usefull for confirming that config
    behaviour is as expected, and is not meant to be useful.
    """

    return toolbox.config_from_settings(sources=sourcelist, additional_values=additional_values)


@pytest.fixture()
def loaded_config(config):
    """LoadedConfig object loaded from the test config using the 'test' key"""

    return config.load("test")

""" TESTS """

def test_sourcelist(tmp_path, sourcelist):
    """ test the sourcelist behaviour """

    sources = [(element.key, element.priority, element.handler.name()) for element in sourcelist.get_ordered_sources()]

    assert len(sources) == 7

    assert sources[0][0] == 'fifth'
    assert sources[0][1] ==  90
    assert sources[0][2] == os.path.join(tmp_path, 'fifth')

    assert sources[3][0] == 'third'
    assert sources[3][1] ==  75
    assert sources[3][2] == os.path.join(tmp_path, 'third')

    assert sources[6][0] == 'fourth'
    assert sources[6][1] ==  9
    assert sources[6][2] == os.path.join(tmp_path, 'fourth')


def test_basic_combined(loaded_config):
    """ test some basic file combining by the config object """

    assert loaded_config.get("1") == "one" # files_data[0]["data"]["1"]
    assert loaded_config.get("2") == "two" # files_data[1]["data"]["2"]

def test_dot_notation(loaded_config):
    """ Confirm that we can retrieve data using the dot notation """

    assert loaded_config.get("3.1") == "three-one" # files_data[2]["data"]["3"]["1"]

def test_overrides(loaded_config):
    """ confirm that keys defined in more than one source get overriden """

    assert loaded_config.get("4") == "four-from-one" # files_data[0]["data"]["4"]
    assert loaded_config.get("5.1") == "five-one from five" # files_data[4]["data"]["5"]["1"]

# @TODO write tests for complicated overrides (arrays/mixed)


def test_variable_templating(loaded_config):
    """ confirm that values can contain template references to other values """

    assert loaded_config.get("7") == "one"
    # test replacement from the same label/source

    assert loaded_config.get("8") == "one from five"
    # test replacement from a different source

    assert loaded_config.get("9") == "default"
    # test formatting default values

    #assert loaded_config.get("10", strip_missing=True) == ""
    # test strip missing values - NO LONGER AN OPTION

    assert loaded_config.get("11") == "megadefault"
    # test a bunch of things tofether

    assert loaded_config.get("12") == "three from six"
    # test that default doesn't swap a positive search

def test_additional_values(loaded_config, tmp_path):
    """ test that .get() can retrieve paths and additional configs """

    assert loaded_config.get("100") == "one-hundred from additional"
    # test get from additional

    assert loaded_config.get("6") == "six from additional"
    # test additional config takes precedence over config

    assert loaded_config.get("13") == os.path.join(tmp_path, "fifth")
    # test additional config takes precedence over config

    assert loaded_config.get("14") == loaded_config.get("13")
    # test additional config takes precedence over config

def test_config_format(loaded_config):
    """ test the direct string format options """

    assert loaded_config.format_string("{variables:third?default}") == "three from six"
    # test additional config takes precedence over config
