# environments

An environment is a global base container for a configuration object and a list
of plugins.

Because the environment is globally registered, any code can retrieve it by name.

## An Environmet as a container

The plugins are called fixtures in the scope of an environment, and are managed
as a global abstract list. The environment object can be asked to create more
plugin instances, which are returned but also registered.

## Mutliple environments

A process can register multiple environments without concern, and the enviornments
can exists in parrallel, but it is up to the consumer to keep the environment
configurations separate or to manage the repercussions of shared config.

Plugins themselves may not like sharing config.
