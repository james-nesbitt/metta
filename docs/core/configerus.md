# Configerus

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

Each environment instance is based around a single config object.  You can
use an existing configerus Config, or ask the environment to create one for you.

Every METTA fixture gets access to the environment, and so can access the Config
object directly.
Tests can be given the environment object or the COnfig object directly.


## Configerus concepts used

We rely heavily on configerus, but also allow any consumers to do the same.

usefull configerus concepts are:

### 1. overriding of config to create custom senarios

If you config is steup right, you can produce variations in test implementaiton
by the inclusion of different config sources.  this can make the variation
easier to parametrize and more obvious as config sources can be named after the
variation.

### 2. deep config strucures that can be validated

Parametrizing with config allows more complex configuration schemas without
having to worry about heavy parametrization of methods.
You can pass a config label and base get key, and then tell your code to use
config to retrieve details.  Then configuration source is managed separately from
parametrization.

If you want validtion, configerus offers plugin based validation of config,
including the option of jsonchema validtion.

### 3. templating for simplifying overrides

If your functionality requires complex configuration, it can be very difficult
to read override scnarios such as tool version changes.  Using templating you
can point complex configuration to contain values from a simpler config layout
and then override just the simpler config.

config/tool.yml
```
tool:
  platform:
    common:
      curl:
        version: "{setup:curl_version}"
```

config/old_curl/setup.yml
```
curl_version: 1.2.2
```
config/new_curl/setup.yml
```
curl_version: 3.2.4
```

@Note that you will have to make sure that you add `config`, and either
`config/old_curl` or `config/new_curl` setup as config sources.
