# Mirantis Testing Toolbox

A set of tools that can be used to create a testing cluster that you can use to
run tests against.

## How to use this toolbox

The toolbox is centered around a configuration system that is meant to allow
simple but advanced configuration for a modular system.  A Config object reads
config from a wide variety of sources which allow overriding, and all of the
other components use the config option to determine behaviour.

First define a list a list of Config Sources, and create a Config object from it

```
import mirantis.testing.toolbox

source_list = mirantis.testing.toolbox.new_sources()
source_list.add_filepath_source(__DIR__)

config = mirantis.testing.toolbox.config_from_source_list(source_list)

```

Now you can create the other useful plugin components that do the work

```
provisioner = mirantis.testing.toolbox.provisioner_from_config(config)

```

That provisioner is created using passed config, and if properly configured can
manage your cluser

```
provisioner.up()

test_my_system()

provisoner.down()
```

## Config

simple config handler, used to allow simple overriding collective configuration
from files in different paths.

The purpose of the Config object is to be a flexible common source of
configuration that can be passed around and consumed by any part of the testing
system.

## Plugins

Plugins are injected code which can take over a known role for the toolbox. They
are defined in any package/distribution using setuptools entry_point entries
that use the known plugin names.

Currently the plugin loader only loads known plugin types based on an enumerator
in `plugin.py`
A plugin entry_point is expected to be a factory which will return an object
based on configuration that it loads itself from a passed Config object

@see `plugin.py` for the interface definition. The interface is never applied
but can give an idea to developers how to develop plugins

### Provisioners

Provisioners are responsible for testing cluster management.

Provisioner functionality can be grouped into the following categories:

#### Cluster Management

Bringing a cluster up, and tear it down

#### Cluster interaction

Interacting with the services and hosts on a cluster.

### Clients

Client plugins are used to interact with testing clusters.  They can be used to
execute code in a system or to interact with an API or service.

Clients are typically provided by provisioners/

```

docker_client = provisioner.get_plugin("docker")
k8s_client.run( ... )

kubernetes_client = provisioner.get_plugin("kubernetes")
coreV1 = kubectl_client.get_CoreV1Api_client()

ns = coreV1.read_namespace(name="kube-system")
```

### Workload

Workload plugins define a workload that can be applied to a testing cluster
