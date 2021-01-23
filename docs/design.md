# Design

MTT is based around a plugin system, and a dynamic configuration system.

The plugin system attempts to be modular and allows injection of external
depenencies using python decorators to register plugin factories.

The config system allows loading of various sources of configuration, such as
files from various folders, and dicts.  The various sources are priorities and
deep merged to allow higher priorty values to override lower priority values

For more details look at the `./core` documentation.

# Using configuration overrides to dynamically configure

Variations in cluster configuration is facilitated by adding overriding sources
to customize values.

Overriding can happen at startup or while you are using the toolbox.
