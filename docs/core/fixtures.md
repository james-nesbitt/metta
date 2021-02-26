# Fixtures

Fixtures are wrapped METTA plugins, with metadata about their context.

## Fixtures object

Fixture instances exist in a Fixtures list object, which can handle retrieval
with consideration of filtering and sorting based on priority

Some aspects of a Fixture instance have no meaning outside of the Fixtures object
(e.g. priority)

### Searching

You can ask the Fixtures object for a subset or single Fixture or plugin based
on Fixture metadata.

## Fixture object

A Fixture object wraps the plugin object with metadata usable for introspection
or fitlering/searching/sorting.

1. type : METTA plugin type (metta.plugin.Type) ;
2. plugin_id : METTA Plugin id as registered with the plugin factory;
3. instance_id : arbitrary METTA Plugin instance label for this object instance;
4. priority: sorting integer (1-100) to allow sorting to be defined on the fly.

The fixture also contains the plugin instance at `.plugin`

## Creating fixtures in a test suite


There many ways to ask an environment object to create fixtures, in batches or
one at a time.  The environment has several handlers to receive config pointers
or dicts of information for a plugin.

A common pattern to use is to create a `fixtures.yml` file/source that contains
an array/list of fixture definitions.  Pass the label/base for a fixtures list
to the environment to the environment `add_fixtures_from_config` methid, which
assumes the root of fixtures as a default.

@see the environment object for other options.

## A fixture from config/dicts

The general minimum information needed to define a fixture looks like:
```
type: metta.plugin.output
plugin_id: my_plugin
```

Where this information correlates with the plugin factory decoration arguments,
and tell metta what plugin to load.

You can also define additional values such as:

```
arguments:
  one: 1
  two: 2
```

Which will send `(one=1, two=2)` to the plugin factory method.  If the plugin
factoty doesn't like the arguments it will likely generate an exception.

A common pattern for plugins is that they configure themselves from config,
instead of from constructor arguments.  In this case, they receive config pointers
for `label` and base `key` which they use to load configuration.  This allows
separation of parametrization details and "where is my config.".
Such plugins can use:
```
arguments:
  label: my_label
  base: path.to.my.config
```
Or the more explicit form:
```
from_config:
  label: my_label
  base: path.to.my.config
```

In cases where the same config used to build the plugin should be consumed by the
plugin itself, a value of `from_config: true` will tell any environment object
building fixtures from config to pass the correact label and key pair on.
