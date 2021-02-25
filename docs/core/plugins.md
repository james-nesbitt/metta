# Plugins

Anything that could be turned into a plugin was turned into a plugin.

Plugins provide the majority of functionality.

A plugin is registered by decoration, meaning that a consumer must first import
the decoration before it can be used. The decoration is for a plugin factory,
which by convention is put into a package __init__.py along with other utility
functions so that consumer can import just the package.


## Why this pattern

This allows types of plugins to come from anywhere, and can be injected at runtime
with minimal interaction.

Typically you don't load a plugin yourself, but rather you put the plugin id
into config somewhere and metta reads that and knows what to load.
The plugin system is flexible as it can receive dynamic construction arguments
but is still registered and available for introspection.

You still have to import any modules/packages which decorate the plugins,
but it is a leaner approach.

## Plugin factory pattern

The decoration factory patter typically looks like this;

A plugin class is defined, as an extension of the BaseClass it extends.  The
plugin is registered with metta by being decorated using an metta Factory decorator

If you can import your decoration, then the plugin is avaialble.

## Bootstrapping

setuptools based injection/registration is also possible if you pass a setuptools
bootstrap key into the environment boostrap list.

This can be used to both import he decoration but also to modify the environment.

## Plugin usage

### Creating a plugin instance

Plugins are expected to only be created by an environment object.  This
requirement enables introspection, and allows plugins to dynamically require
other plugins which are in the same scope.

You typically create plugins as individual fixtures, or as lists of fixtures by
passing dict or configerus (label/key) info to the environment.
The environment info needs to contain enough to define which plugin should be
created, and can include some option constructor arguments.  The environment
object crates the plugin and registers it as a fixture.

### Plugin anatomy

Plugins can be very unique but need to fit into METTA overall. As such they need
the following interface.

1. All plugins should be build using a factory function, which should return a
   plugin object.

2. All plugin factory methods will be given an environment object and a string
   instance_id for that instance.

3. Any plugin factory can expect other constructor arguments. It is best if these
   are optional arguments as their construction is usually done by passing
   arguments from configuration.

4. Any plugin can implement an `info()` method which can return dict data about
   the plugin for introspection.
