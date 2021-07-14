# Custom Plugins

The demo shows how easy it is to write a custom plugin and have it included
into a source base dynamicaly.

In this case it may look like a longwinded method to get some code injected,
but when it is considered in combination it should be clear how it can be
parrallel.

## The custom plugin

The plugin is defined in `.plugins/custom.py`.  There we have both of the
critical components for injecting plugins as fixtures:

1. the Factory decoration which registers the plugin with metta;
2. the plugin class which will be created when the fixture is requested.

## How does the injection work

First you should look at the `metta.py` module which creates metta environment.
Of particular note is:

1. the includsion of the `metta_common_config` bootstrap id which tells metta to
   add the ./config folder as a source of config.
2. The python import of `plugins/custom` which imports the custom plugin folder
   in both any `python -m ` and `metta` CLI context.  Importing the module
   executes the decorator which registers the plugin.
3. The config `fixtures,yml` file includes a definition of an instance of the
   plugin by the name `my_messages`.
4. In `metta.py` the environment is told to load any fixtures in `fixtures.yml`

## Running

You can execute the code in standard python ways:
```
$/> python -m main.py
```

But you can also use the `metta` CLI to inspect the environment:

```
$/> metta config get fixtures
```
should show you the contents of your fixtures file

```
$/> metta config sources
```
will show you the list of sources which are providing config for your
environment.

```
$/> metta fixtures info --instance_id my_messages --deep
```
Will show you the output of your plugin info()
