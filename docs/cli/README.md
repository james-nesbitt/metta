# METTA - the cli

There is a CLI tool that can be used with METTA.  The idea is that because it can
be hard to confirm METTA confioguration and fixture status when embedding METTA
into your testing system, the CLI can give you introspection and interaction to
confirm assumptions or even as a part of automation with a custom non-python
test harness.

## Using METTA with your testing code

The only complication is telling METTA how your environment is defined.

METTA looks across parent folders for a mettac.py or metta.py file. If it is found
then that path is considered the root of your test suite, and that code is
imported as a module AND IS EXPECTED TO DEFINE AN ENVIRONMENT.

For some scenarios this can complicate your code as the metta.py file is imported
without namespace context and so can't import its neighbours easily.
A common technique is to define your environment in the file and then your test
harness can import it and then use metta.get_environment to get access to the
enviroment instance.

## Design

The cli has a bootstrapping phase where it tries to discover the metta.py file
but then it implements its functionality via the CLI Type UICTT plugins.
Any registered plugin can provide CLI functions.

The CLI is based on the Fire CLI framework, so CLI plugins should have a `fire()`
method which returns a dict of commands/groups which are added to the fire
context.  The CLI plugins all get access to the environment objects.

The METTA core provised a number of plugins, but contrib modules also provide
their own (with some healthy repetition)

In scenarios with multiple environments, there should be a way to tell the
CLI which environment to use, but that is not yet implemented.

### Methods

#### Information methods

These are introspection methods meant to be used to discover your METTA setup.
These plugins generaly try to return indented json, in order to be machine
consumable.

#### Operation methods

These methods make changes to the test infrastructure.  Their output tends to
be related to the changes, and is not generally machine consumable.

## Plugins

### Core

#### Info

a small stub sanity cli plugin that requires little, and offers little use.

#### Environment

A small plugin that can list configured environments.  This is useful for
scenarios where you are using multiple environments.

#### Config

This plugin let's you investigate the configuerus setup.  It lets you:

1. list all configerus plugins included;
2. list all configerus  cconfig sources included, including some deeper options
3. retrieve a list of config labels that have been loaded
4. retrieve any actual config target, with overrides and formatting completed.
5. format a passed in string to configm templating in place

#### Fixtures

This cli plugin lets you confirm all created METTA fixtures. Some plugins provide
deeper introspection information which can be included.

#### Provisioner

For specifically provisioner fixtures, this cli plugin lets you discover plugins
but also allows you to run the infra management methods such as prepare() and
apply().

#### Output

For specifically output plugins, this cli plugin lets you discover plugins but
also investigate any avaialble output.

### Contrib

These are CLI plugins provided by contrib modules.  The are typically found in
`metta contrib <command` group.

Most common are the contrib provisioner CLU plugins such as terraform and ansible
which behave the same as the provisioner command group, but also include plugin
specific methods.

These plugins may not present if they detect no matching plugin fixtures.
