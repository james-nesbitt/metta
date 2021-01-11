""" Config

## Combining

Combining is the act of loading all config (files) for a particular label (or
matching file-name) and then merging the various sources into a single set.
This allows some sources to set defaults that are overriden in higher priority
sources

The rules for combining are:
1. sources are merged as maps, combining deeply combing distinct keys
2. duplicate keys of maps/arrays will combine
3. duplicate keys of basic primitives take the higher priority source value

It is not perferct, but it can be worked with to provide a decent config
system.  it's strengths are that it is flexible without being overly complex.
It takes a few tricks to make it really strong:

1. Separate out config into different "labels" (filename) as overriding is simpler
   and config from one label can reference another.

   Examples:
     config.json       <-- core config
     provisioner.json  <-- config related to a core topic
     terraform.json    <-- config that a specific module/object needs
     variables.json    <-- general parametrization
     secrets.json      <-- privileged parametrization

2. Vary configuration using paths

    to allow different configuration scenarios, include different sets of paths
    per scenario to allow scenario specific configuration to override core
    defaults

    Example:

    config.json
    project.json
    variables.json

    -- scenario_1
        variables,json

    -- scenario_2
        variables.json
        project.json

3. Parametrize configuration for easier overrides

    Nested Dict merging is not a pretty science, so trying to override complex
    configuration structures can get messy.
    Consider templating in complicated structures into more flat parameter
    sources, and overriding in those simpler cases.

4. config paths are usefull for module/package/distribution interactions

    The config objects can return the keyed paths that they use to load data.
    These paths can contain more than just config, and perhaps the paths are
    usefull for other code.

    An example is a provisioner template.  If you are using a plugin that needs
    a path to a provisioner template, and it is in the project path, the config
    object can provide that path directly to the plugin as a key without the
    code needing absolute awareness of cwd.

ToDo:

1. why limit ourselves to files?  Remote APIs for things like vault could also
   provide data

2. revisit the Dict merging code to see if it behaves in a way that people want

3. should load be able to reprioritize paths? for single cases?  Sometimes we
   don't like the order .

"""

import logging
from typing import Any, List, Dict
from collections import OrderedDict
import re
from .tools import _tree_merge, _tree_get
from .config_sources import SourceList

logger = logging.getLogger("mirantis.testing.toolbox.config")

CONFIG_DEFAULT_MATCH_PATTERN = r'\{((?P<source>\w+):)?(?P<key>[\w.]+)(\?(?P<default>[\w]+))?\}'
""" Default regex pattern used to string template, which needs to identify
keys that can be used for replacement. Needs to have a named group for
key, and can have named group for source and default

The above regex pattern resolves for three named groups: source, key and default:

the {first?check} value          : key=first, default=check
a {common.dot.notation} test     : key=commond.dot.notation
a {label:dot.notation.test} here : source=label, key=dot.notation.test

so:
1. all replacements are wrapped in "{}"
2. an optional "source:" group tells config to look in a specifig label
3. a "?default" group allows a default (untemplated) value to be used if the
   key cannot be found
"""

class Config:
    """ Config management class (v2)

    Allows some sourced file based project configuration with some pattern
    templating and path set overriding.

    To allow easy separation of config into manageable files, all config is
    grouped into "label" strings which correlate to config files with matching
    names.
    Before accessing a config label, it has to be loaded, which you can do with
    the load() method.
    Then all get() calls use the most recently loaded config label.

    Templating: some string substitution can be done based on config values
        and some path keys. Templating options are based on a custom syntax

    Overriding: tell config about multiple paths in order of priority, and it
        will allow higher priority values to override lower priority values

    Dot notation retrival: you can treat your data as a tree, and config will
        allow you to retrieve tree nodes using a syntax where "." is a node
        label delimiter.


    @TODO allow more overrides of the templating system such as alt regex
    """

    def __init__(self, sources: SourceList):
        """ Constructor

        Arguments
        ---------

        sources -> SourceList:
            a list of sources for retrieving config

        """

        # save all loaded config when it is first loaded
        self.loaded = {}
        """ LoadedConfig map for config that has been loaded """

        self.sources = sources
        """ sources to be used for config loading """

    def _get_config(self, label: str):
        """ internal method that loads data from all of the sources for a label """

        logger.debug("Loading Config '%s' from all sources", label)

        data = {}
        # merge in data from the higher priorty into the lower priority
        for source in self.sources.get_ordered_sources():
            source_data = source.handler.load(label)
            data = _tree_merge(data, source_data)

        if not data:
            raise KeyError("Config '%s' loaded data came out empty", label)

        return data

    def reload_configs():
        """ Get new data for all loaded configs

        In case it isn't clear, this is expensive

        """
        logger.debug("Config is re-loading")
        for label in self.loaded.keys():
            data = self._get_config(label)
            self.loaded[label]._reload(data)

    def load(self, label: str, force_reload: bool=False):
        """ Load a config label """
        if force_reload or label not in self.loaded:
            if label == "_source_":
                # This is a special case where the config source being requested
                # is actually the source list itself, for those that have names
                data = {}
                for name in self.sources.source_names():
                    source = self.sources.source(name)
                    if source:
                        data[name] = source.handler.name()
            else:
                data = self._get_config(label)

            if label in self.loaded:
                self.loaded[label]._reload(data)
            else:
                self.loaded[label] = LoadedConfig(data=data, parent=self)

        return self.loaded[label]


class LoadedConfig:
    """ A loaded config which contains all of the file config for a single label

    This is an easier to use singe label config object from which you can get
    config using dot notation.

    Think of this as relating to a single filename, merged from different paths
    as opposed to the Config object which loads config and hands of to this one.

    """

    def __init__(self, data, parent):
        """
        parameters
        ----------

        data (Dict[str, Any]): deep dict struct that contains all of the merged
           configuration that is te be used for config retrieval. It is often
           a nested Dict with standard primitives as can be loaded from json/yml

        parent (Config): The parent Config object which created this object
           which is used for backreferencing, primarily when trying to perform
           template string substitution as substitution can refer to config from
           other sources.

        """

        self.data = data
        self.parent = parent

    def _reload(data):
        """ Allow new data to be passed in

        this is meant to be used by the core only, and is used to update config
        when new config paths are added, typically by boostrapping.

        Hopeully this is done before the config is really used

        """

        self.data = data

    def get(self, key: str, format: bool=True, exception_if_missing: bool=False):
        """ get a key value from the active label

        Here you can use "." (dot) notation to indicated a path down the config
        tree.
        so "one.two.three" should match the descending path:

        one
        --two
            --three

        Parameters:

        key (str): the dot notation key that should match a value in Dict

        format (bool): should retrieved string values be checked for variable
           substitution?  If so then the str value is checked using regex for
           things that should be replaced with other config values.
           @see self.format_string()

        Returns:

        (Any) anything in the Dict is a valid return.  The return could be a
            Dict with child elements, an array or any other primitive.
            If the return is a string then it is formatted for variable
            substitution (see self.format_string())

        Throws:

        Can throw a KeyError if the key cannot be found (which also occurs if
        all sources produced no data)
        """

        value = ""

        try:
            value = _tree_get(self.data, key)
        except KeyError as e:
            if exception_if_missing:
                # hand off the exception
                raise e
            else:
                logger.debug("Failed to find config key : %s", key)
                return None

        # try to format any string values
        value = self.format_value(value)

        return value

    def format_value(self, target, strip_missing: bool = False):
        """ Nested formatter for Any types """
        if isinstance(target, Dict):
            target = self.format_dict(target, strip_missing)
        elif isinstance(target, List):
            target = self.format_list(target, strip_missing)
        elif isinstance(target, str):
            target = self.format_string(target, strip_missing)

        return target

    def format_string(self, target: str, strip_missing: bool = False):
        """ Replace all "template variables" in the passed string with any
        found values in config.
        Think "".format() but with named patterns in the string that correlate
        to config values.

        this function is primarily usefull internally, but it could be useful
        publicly, so it is made public.

        The process here is effectively a regex sub for any pattern matches by
        treating match returns as config keys.
        Keep in mind that the pattern used is configurable, but by default, the
        function looks for "{key}" and then looks up the key in the config.
        If the config contains a ":" then the string before the token is
        considered a config key/label, and that config label is loaded

        Why do this?  Well it allows more separation of values across config
        sources, it allows some sources to be more privileged than others and
        it allows easier overrides.
        """

        # leave self in context for the closure
        c = self
        def find_replacement(match):
            """ find the re_sub results """
            if match.group('source') is not None:
                source = c.parent.load(match.group('source'))
            else:
                source = c

            key = match.group('key')
            try:
                sub = source.get(key, exception_if_missing=True)
                return sub
            except KeyError as e:
                if match.group('default'):
                    return match.group('default')
                elif strip_missing:
                    return ''
                else:
                    # if a template string wasn't found then exception
                    raise e

        return re.sub(CONFIG_DEFAULT_MATCH_PATTERN, find_replacement, target)

    def format_list(self, target: List[Any], strip_missing: bool = False):
        """ format all strings in a List """
        for index, value in enumerate(target):
            target[index] = self.format_value(value, strip_missing)
        return target

    def format_dict(self, target: Dict[str, Any], strip_missing: bool = False):
        """ format all strings in a Dict """
        for key, value in target.items():
            target[key] = self.format_value(value, strip_missing)
        return target
