# Getting Started

## Getting it installed.

Normally you would install as any python module using pip.  MTT is not (yet)
registered as a pip package so you have to do it the old way.

```
git clone {mtt repo} mtt
cd mtt

pip install .
```

If you are developing then consider using `pip install -e .` to get it editable.

## Use MTT in python code

With MTT installed, you now need to write an application which imports it.

You are going to want to start by creating a Config object and using that to get
a provisioner object

```
import mirantis.testing.mtt as mtt
# Import any modules with decorators that you want activated
import mirantis.testing.mtt_common as mtt_common
import mirantis.testing.mtt_mirantis as mtt_mirantis
# Maybe we'll ask for a docker client later
import mirantis.testing.mtt_docker as mtt_docker

# we will use these as well
import datetime
import getpass

# New config
config = mtt.new_config()
# Add ./config path as a config source
config.add_source(mtt_common.MTT_PLUGIN_ID_CONFIGSOURCE_PATH, 'project_config').set_path(os.path.join(DIR, 'config'))
# Add some dymanic values for config
config.add_source(mtt_common.MTT_PLUGIN_ID_CONFIGSOURCE_DICT, 'project_dynamic').set_data({
    "user": {
        "id": getpass.getuser() # override user id with a host value
    },
    "global": {
        "datetime": datetime.now(), # use a single datetime across all checks
    },
    config.paths_label(): { # special config label for file paths, usually just 'paths'
        "project": __DIR__  # you can use 'paths:project' in config to substitute this path
    }
})

# provisoner from config
prov = mtt.new_provisioner_from_config(config, 'ltc_provisioner')
```

That code will read a whole bunch of config.

To get a provisioner, you are going to need at least the following:

'provisioner.py':
```
plugin_id: {what backend plugin do you want to use}
```
(check what else your particular provisioner expects)

## What can I do with it

Use it to start up cluster resources

```
prov.prepare()
prov.apply()

prov.get_client(mtt_docker.MTT_PLUGIN_ID_DOCKER_CLIENT)

# do some docker stuff
ps = docker_client.containers.list()
```

And lot's more.

Don't forget to tear it all down.

```
prov.destroy()
```

## What more

take a look at the `./demos`.  You can find some examples there of some very
simple feature elements, and also some full featured testing demos
