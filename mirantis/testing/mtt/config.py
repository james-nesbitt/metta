import logging
from typing import Any, List, Dict
import re
from .plugin import MTTPlugin, Type as PluginType, Factory as PluginFactory
from .shared import tree_merge, tree_get

logger = logging.getLogger("mirantis.testing.toolbox.config")

MTT_PLUGIN_ID_CONFIGSOURCE = PluginType.CONFIGSOURCE
""" Fast access to the ConfigSource plugin_id to allow minimal imports """

class MTTPluginConfigSource(MTTPlugin):
    """ Base class which all ConfigSource plugins should extend

    **we could move this to its own file for readability, but it would
      only complicate consumer imports**

    """

    # __init__ from MTTPlugin

    """ INTERFACE Definitions

    If you don't override these methods then you will get an exception """

    def load(label: str):
        """ Load a config label """
        raise NotImplementedError("MTT ConfigSource plugin did not implement load()")

    """ Utility methods usable by extenders"""

    def tree_merge(self, source: Dict[str, Any], destination: Dict[str, Any]):
        """Deep merge source into destination"""
        return tree_merge(source, destination)

    def tree_get(self, node: Dict, key: str):
        """ if key is a "." (dot) delimited path down the Dict as a tree, return the
        matching value, or throw an exception if it isn't found """
        return tree_get(node, key)


CONFIG_DEFAULT_MATCH_PATTERN = r'\{((?P<source>\w+):)?(?P<key>[\w.]+)(\?(?P<default>[^\}]+))?\}'
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

MTT_CONFIG_PATH_LABEL = 'paths'
""" If you load this label, it is meant to be return a keyed path """

CONFIG_SOURCE_DEFAULT_PRIORITY = 75
""" Default source priority, which should be a common unprioritized value

General approach:

<35 Low priority defaults (system)
<50 Higher priority defaults (contrib)
<75 Low prority setting (project)
 75 default
<90 High priority settings (project, contrib)
>90 !important (project)

"""

class Config():
    """ Config management class (v3)

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

    def __init__(self):
        self.sources = {CONFIG_SOURCE_DEFAULT_PRIORITY: []}
        """ Keep the collection of config sources  in a Dict where the keys are
            priority and the values are a list of Source plugins at that priority
        """

        # save all loaded config when it is first loaded to save load costs on repeat calls
        self.loaded = {}
        """ LoadedConfig map for config that has been loaded """

    def copy(self):
        """ return a copy of this Config object """
        logger.debug("Config is copying")
        copy = Config()
        copy.sources = self.sources.copy()
        return copy

    def add_source(self, plugin_id: str, instance_id: str = '', priority: int=CONFIG_SOURCE_DEFAULT_PRIORITY):
        """ add a new config source to the config object and return it

        Parameters:
        -----------

        plugin_id (str) : id of the plugin as registered using the plugin factory
            decorater for a source plugin.  This has to match a plugin's registration
            with the plugin factory as a part of the Factory decoration

        instance_id (str) : Optionally give a source plugin instance a name, which
            it might use for internal functionality.
            The "path" source plugin allows string template substitution of the
            "__paths__:instance_id" for the path.

        priority (int) : source priority. Use this to set this source values as
            higher or lower priority than others.

        Returns:
        --------

        Returns the source plugin so that you can do any actions to the plugin that it
        supports, and the code here doesn't need to get fancy with function arguments

        """
        source_fac = PluginFactory(MTT_PLUGIN_ID_CONFIGSOURCE, plugin_id)
        source = source_fac.create(self, instance_id)
        if not priority in self.sources:
            self.sources[priority] = []
        self.sources[priority].append(source)
        self.reload_configs()
        return source

    def paths_label(self):
        """ retrieve the special config label which is a list of paths """
        return MTT_CONFIG_PATH_LABEL

    def default_priority(self):
        """ Return the default priority for relative priority setting """
        return CONFIG_SOURCE_DEFAULT_PRIORITY

    def has_source(self, instance_id:str):
        """ Check if a source instance has already been added

        You can use this in abstracts to detect if you've already added a config

        """
        for priority in self.sources.keys():
            if instance_id in self.sources[priority]:
                return True
        return False;


    def load(self, label:str, force_reload:bool=False):
        """ Load a config label

        This queries all sources for the label and merges the loaded config data
        into a single LoadedConfig object.
        The loads are cached per Config instance to make repeated calls cheap.

        Parameters:
        -----------

        label (str) : Config label to load.  Every config source can provide
            config data sets for labels, which correspond to things like
            "all files with a matching filename", or all "records in a matching
            db table"

        force_reload (bool) : if true, and data has been loaded before, this
            forces a fresh reload of data from the sources

        Returns:
        --------

        A LoadedConfig object from which you can .get() specific pieces of config

        Throws:
        -------

        Some source plugins will throw Exceptions if they have internal problems

        """
        if force_reload or label not in self.loaded:
            data = self._get_config_data(label)
            self.loaded[label] = LoadedConfig(data=data, parent=self)

        return self.loaded[label]

    def reload_configs(self):
        """ Get new data for all loaded configs

        In case it isn't clear, this is expensive, but might be needed if you
        know that config has changed in the background.

        """
        self.loaded = {}

    def _get_config_data(self, label: str):
        """ load data from all of the sources for a label """
        logger.debug("Loading Config '%s' from all sources", label)

        data = {}
        # merge in data from the higher priorty into the lower priority
        for source in self._get_ordered_sources():
            source_data = source.load(label)
            data = tree_merge(data, source_data)

        if not data:
            raise KeyError("Config '{}' loaded data came out empty.  That means that no config source could find that label.  That is likely a problem".format(label))

        return data

    def _get_ordered_sources(self):
        """ retrieve a flat List of config sources ordered high to low by priority """
        ordered = []
        """ Keep the uber list of sorted sources """
        for priority in sorted(self.sources.keys()):
            ordered += self.sources[priority]
        ordered.reverse()
        return ordered

class LoadedConfig:
    """ A loaded config which contains all of the file config for a single label

    This is an easy to useconfig object for a single load. From this you can get
    config using dot notation.

    Think of this as relating to a single filename, merged from different paths
    as opposed to the Config object which loads config and hands off to this one.

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

    def _reload(self, data):
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
            value = tree_get(self.data, key)
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
        """ Nested formatter for Any types, searches for strings for format_string() """
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

        Parameters:
        -----------

        target (str) : string that should be formatted

        strip_missing (bool) : if True then match patterns that cannot be found
            in config will be removed and no exception will be thrown.

        Returns
        -------

        The passed string with all found patterns replaced with config values

        Throws:
        -------

        KeyError if a found pattern has not matched with config (value could
            not be found) IF the pattern had no default suggestion, and
            strip_missing is False
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
                return str(source.get(key, exception_if_missing=True))
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
        """ Search a List for strings to format @see format_string """
        for index, value in enumerate(target):
            target[index] = self.format_value(value, strip_missing)
        return target

    def format_dict(self, target: Dict[str, Any], strip_missing: bool = False):
        """ Search a Dict for strings to format @see format_string """
        for key, value in target.items():
            target[key] = self.format_value(value, strip_missing)
        return target
