# Plugins

Anything that could be turned into a plugin was turned into a plugin.

Plugins provide the majority of functionality.

A plugin is registered by decoration, meaning that a consumer must first import
the decoration before it can be used. The decoration is for a plugin factory,
which by convention is put into a package __init__.py along with other utility
functions so that consumer can import just the package.

For a list of plugin types look in `../plugins`.
For a list of available plugins look at the packages in `../vendor`.

## Why this pattern

This allows types of plugins to come from anywhere, and can be injected at runtime
with minimal interaction.

Typically you don't load a plugin yourself, but rather you put the plugin id
into config somewhere and mtt reads that and knows what to load.
The flexibility comes from the fact that the plugin receives a config object
which it can use to configure itself.

You still have to import any modules/packages which decorate the plugins,
but it is a leaner approach.

## Plugin factory pattern

The decoration factory patter typically looks like this;

A plugin class is defined, as an extension of the BaseClass it extends.  The
plugin is registerd with mtt by being decorated using an mtt decorator 


## v0.1.0 plugins

The original patter for plugin was to use setuptools entrypoints for injection
at install time of plugins.  This allowed fewer imports but was weak for boot
strapping, and is probably considered an outdated method for python.
