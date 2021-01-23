# Config

Config is about providing a common system that can be used to read and combine
any config from various sources and making it easy to retrieve.

Config is effectively Deeply Merged Dicts.  The merge sources are the prioritized
source plugins.  Two plugins are included in core: one which read json and yaml
files in a path, and the other which lets you pass in a Dict of values.

With a config object, you can retrieve all merged data for a label (like all files
in a set of paths with the same name) and from there you can retrieve tree nodes
using a dot-notation syntax.

Additionally, the loaded config has a built in templating system that allows deep
string substitution with a syntax that lets you inject one value into another.
It's not very sophisticated, but it does offer some interesting extendable
functionality.

Sounds complicated?  It's actually not.

## Why

Well, it's nice to be able to merge data from different files of the same name
in different paths, so that you can one file set defaults, and another override
just some parts.
At run time you can do some fun tricks like including a path for a variation of
your setup which will overwrite config to add the variable settings.

Mix this in with the string substitution and you can focus overrides on simple
config, and inject the overriden values into more complex config.

The json/yaml plugin means that you can focus toolbox functionality in flat files
and determine your own patterns, but it also lets the toolbox implement some
core patterns that you can use to configure it.

The Dict plugin lets you dynamically determine values that you may not want or
be able to put into files.

## Usage

Start with an empty config object (using __init__.py new_config() is best)

```
import mirantis.testing.mtt as mtt

conf = mtt.new_config()
```
(conf actually assigns some common config sources if you let it)

Then add some sources of your own:
```
import os.path
import datetime

global_overrides = {
    'global':{
        'project': 'my-project',
        'username': 'my-name', # use getpass for this
        'password': secret_var,
        'datetime': datetime.now(),
        'options': {
            'project-key': "{project}-{username}"
        }
    }
}

conf.add_source('path', 'project_config').set_path( os.path.dirname(os.path.realpath(__file__)) )
conf.add_source('dict', 'overrides', conf.default_priority()+5).set_data( global_overrides )

```

Now you can load and retrieve config:
```
# load all 'global' from all sources (key from the dict, and any global.json|yaml files)
global_conf = conf.load('global')

assert global_conf.get('project') == 'my-project'
assert global_conf.get('options.project-key') == 'my-project-my-name'
```

## Source plugins

Actual configuration loading is performed by

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

## Templating

String substitutions are performed on any retrieved strings, during the .get()
call (unless directed not to.) The string is analyzed using regex and then
replacements values are requested.

@see CONFIG_DEFAULT_MATCH_PATTERN for the pattern

When finding a potential replacement match, the match can specify:
1. a default value if the key cannot be found
2. a particular config label that contains the value if the config object should
   load a different label
3. the loaded config key for the replacement value

An exception is raised if the value cannot be found and no default was provided.

## Concepts

config object : can load and combine  config from a set of prioritized sources

config load : retrieve config from a backend for a label, like loading a single
    file that matches the label

config combine : merge config for one label from different backends with a
    priority for the handlers

source handler/plugin : an MTT plugin that knows how to load config from a single
   place

source list : a prioritized set of source handlers

priority : we use a 1-100 integer priority value, large == higher priority

config get : retrieve arbitrary data from a laoded config

templating : substitute some config values into a string based on some regex

## ToDo:

1. why limit ourselves to files?  Remote APIs for things like vault could also
   provide data

2. revisit the Dict merging code to see if it behaves in a way that people want

3. should load be able to reprioritize paths? for single cases?  Sometimes we
   don't like the order .

"""
