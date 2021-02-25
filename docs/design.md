# Design

METTA is based around a plugin system, and a dynamic configuration system.

The plugin system attempts to be modular and allows injection of external
depenencies using python decorators to register plugin factories.

The config system allows loading of various sources of configuration, such as
files from various folders, and dicts.  The various sources are priorities and
deep merged to allow higher priorty values to override lower priority values

For more details look at the `./core` documentation.

## Using configuration overrides to dynamically configure

METTA heavily relies on configerus configuration to allow a dynamic testing
system.
Some configuration is very common but all of it is optional, as the environment
object can be configured in many different way
