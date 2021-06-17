# METTA Cli

A python fire base cli manager that uses metta plugins to create commands to
interact with METTA environments at the command line.

The original goal for the cli was to support testing engineers who use METTA in
testing systems to discover and interact with the METTA components for debugging,
as the config and fixtures can be hard to debug.
The CLI has grown to be usefull enough taht it could play a role in a test
system on its own

## Design

the metta.contrib.cli.entrypoint:main is used as a setuptools entrypoint for
running the commands.

Bootstrapping happens in the following stages:

1. Look for a root context by scanning parents folders until we find a metta.py
   or mettac.py.  That file is laoded as a module, and is expected to bootstrap
   a METTA environment.

2. All CLI plugins that have been registered during bootstrapping are created
   and asked for cli commands, which are added to scope.

3. Fire CLI takes over and interprets your cli arguments as commands.

## Usage

When you isntalled the metta package, the `mettac` cli should have been installed
as a setuptools entrypoint.  Your system should have put a python executable
shim in a good place.

Call the ucct directly to list commands:
```
$/> mettac --help
```

Commands are grouped, but all should have some modicum of help with `--help`.

## Commands

As CLI pugins can come from anywhere, this list could be incomplete.

Some contrib packages such as terraform, and ansible will only add commands if
they detect related fixtures in the environment.
If your METTA Cli environment was properly bootstrapped, then the cli should be
able to interact with config and fixtures easily.

### Config

This command is very usefull as it can show you then end contents of your config.

Knowing what config .load() and .get() will retrieve you allows you to have
certainty in systems where a large number of config sources may have made config
state unclear.
There are also Config commands for seeing all of the added sources, for seeing
what .load() labels have been loaded, and even for formatting a string using
config.

### Fixtures

The Cli fixtures command group will allow you to discover what fixtures have
been created in the environment.  You should be able to discover fixture
metadata, and if a plugin has an `info()` operation then more information can
be provided.
