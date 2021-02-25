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
