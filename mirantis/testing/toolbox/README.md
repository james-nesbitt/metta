# Mirantis Testing Toolbox

## config

simple config handler, used to allow simple overriding collective configuration
from files in different paths.

The purpose of the Config object is to be a flexible common source of config
that can be passed around and consumed by any part of the testing system.

## Plugins

Plugins are injected code which can take over a known role for the toolbox. They
are defined in any package/distribution using setuptools entry_point entries
that use the known plugin names.

Currently the plugin loader only loads known plugin types based on an enumerator
in `plugin.py`
A plugin entry_point is expected to be a factory which will return an object
based on configuration that it loads itself from a passed Config object

@see `plugin.py` for the interface definition. The interface is never applied
but can give an idea to developers how to develop plugins

### Provisioners

Provisioners are responsible for testing cluster management.

Provisioner functionality can be grouped into the following categories:

#### Cluster Management

Bringing a cluster up, and tear it dowm

#### Cluster interaction

Interacting with the services and hosts on a cluster.
