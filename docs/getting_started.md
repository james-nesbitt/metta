# Getting Started

## Getting it installed.

```
pip install metta
```

## Use METTA in python code

With METTA installed, you now need to write an application which imports it.

You are going to want to start by creating an environment object
```
import mirantis.testing.metta

env = metta.new_environment(name:'MyEnv')
```

That environment exists globally , and can be retrieved elsewhere using
`metta.get_environment(name:'MyEnv')`

If you already have a configurus.config.Config object, it can be used to directly
create a new environment.

The primary purpose for the environment is to contain a Config object and to
manage fixtures for the environment.  Fixtures for the environment are expected
to come from config.
First you'll need to get some sources of config into the environment

For example, here we add a config source which is a path that can contain files
and a dict of dynamic information

```
# Import configerus for config generation
from configerus.contrib.dict PLUGIN_ID_SOURCE_DICT

# Import the metta core
import mirantis.testing.metta

# Make a new environment
my_env = metta.new_environment(name:'MyEnv')

# Add ./config path as a config source
my_env.config.config.add_source(PLUGIN_ID_SOURCE_PATH).set_path(os.path.join(__dir__, 'config'))
```

The easiest way to get fixtures into the environment is to define them in a
config source such as`./config/fixtures.yml`.

```
my_provisioner:
  plugin_type: provisioner
  plugin_id: dummy

my_client:
  plugin_type: client
  plugin_id: dummy

my_workload:
  plugin_type: workload
  plugin_id: dummy
```

Now METTA can load the fixtures
```
# fixtures from config
environment.add_fixtures_from_config(exception_if_missing=True)
```

Now your environment will have three fixtures; one provisioner, one workload and
one client, all dummy plugins.

## What can I do with it

Use it to start up cluster resources

```
my_prov = my_env.fixtures.get_plugin(instance_id='my_provisioner')

my_prov.prepare()
my_prov.apply()
```

You can also ask a provisioner for client or output fixtures.  You can create
workload fixtures and pass them clients from any fixtures set, and tell them
to start a workload

And lot's more.

Don't forget to tear it all down.

```
my_prov.destroy()
```
