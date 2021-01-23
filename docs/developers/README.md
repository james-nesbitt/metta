# Developers guide

## What code should I write

You can contribute directly to MTT or you can write your own MTT objects in any
python package/module.

If you want to write code to consume in your own testing efforts, then feel free
to write the code in your test-suites or as reusable python modules.
All that is needed to active is to import any modules which contain the mtt
decorater usage.

If you have some code that could be usable to other MTT testers, feel free to
contribute directly to the mtt repository.

Consider the following targets:

### mtt

core functionality for contrib and plugin managing, as well as definition of
types of plugins.
the core is written in such a way that you can throw away the rest of the code
and use it for anything, if you don't like the constraints put in place.

### mtt_common

common functionality that support mtt, but that mtt doesn't need to run, but is
used in most cases.

For example, the config source plugins for path/file and dict are in mtt_common
as is the provisioner plugin for existing backends.

### mtt dummy

Plugins that meet requirements for usage but don't actually do anything.

### mtt_mirantis

Mirantis specific functionality related to our products and how we test.

## Writing a plugin



## Injecting my plugin into my code.
