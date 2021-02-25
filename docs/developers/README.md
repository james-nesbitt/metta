# Developers guide

## What code should I write

You can contribute directly to METTA or you can write your own METTA objects in any
python package/module.

If you want to write code to consume in your own testing efforts, then feel free
to write the code in your test-suites or as reusable python modules.
All that is needed to active is to import any modules which contain the metta
decorater usage.

If you have some code that could be usable to other METTA testers, feel free to
contribute directly to the metta repository.

Consider the following targets:

### METTA

core functionality for contrib and plugin managing, as well as definition of
types of plugins.
the core is written in such a way that you can throw away the rest of the code
and use it for anything, if you don't like the constraints put in place.

### dummy

Plugins that meet requirements for usage but don't actually do anything.

These are usefull for stubbing out components that are not yet delivered, or for
diagnosing misbehaving components, but using dummy plugins to mock out coupling.
The dummy plugins typicaly work by being told how to behave, which means being
told what ind of fixtures to return.

## Writing a plugin

You will need to:

1. write a plugin class, based around receiving an environment object, an
   instance_id, and other (preferably optional) constructor requirements needed
   to operated.

2. write an easy to import factory method for your plugin, and decorate it with
   the METTA plugin Factory decorator, telling the Factory what type of plugin
   and give a plugin_id identity.
   Anyone who wants to use your plugin will need to import the module with the
   decorated factory method.

You can optionally:

1. use the ennvironment config object as needed.

2. discover other fixtures in the environment using the environment object.

### Best Practices

1. Use a configerus label and base key for configuration if you will rely on
  config sources in order to parametrize the plugin.  This allows you to define
  your plugin configration requirements but allows configuration assignment at
  run-time. The config label and key can be you constructor arguments, and can
  default to safe values.

## Injecting my plugin into my code.

### making sure that you plugin is available

All that is needed for someone to use your plugin is that the plugin decorator
is executed.
You can do this by manually importing the  python package.

You can also write a METTA bootstrap setuptools entrypoint which imports the
decorated function, and then include that entrypoint name in the environment
bootstrap list.

The bootstrappers can modify environments when they are created and more.
