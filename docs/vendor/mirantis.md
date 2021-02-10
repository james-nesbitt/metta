# MTT Mirantis

Shared functionality and code that we tend to use at Mirantis

## Plugins

### Launchpad Provisioner

This provisioner plugin will install MCR/MKE/MSR onto a cluster.  The provisioner
uses a backend provisioner to details the cluster.

#### Backend

Currently you have 2 options for a backend provisioner, but any plugin works as
long as is can provide a provisioner `output` which will give the needed yml/dict
that launchpad can use to access the cluster.
This yaml is as per the launchpad specs.

Launchpad owns the backend provisioner, building it itself, and overriding config
that is uses in order to get full access to it.
You can put backend configuration into the launchpad config and the provisioner
plugin will pass it on, or you can let the backend plugin load its own.

Launchpad will call of the needed backend provisioner methods to get the cluster
started and will report any exceptions that occur.

##### 1. use terraform

You can tell launchpad to use the terraform provisioner as its backend. The
terraform plugin will load its own config but you can override it if you want.

The terraform chart is expected to have an output for the launchpad yaml as per
the launchpad documentation.

##### 2. an existing cluster

You can tell launchpad to use the `existing` provisioner as a backend which
you can configure with expected values for output.
Typically this allows you to provision your cluster as needed before running any
testing with mtt, but still have mtt install the product suite.

The existing provisioner takes all outputs and clients as config, so you can just
pass through any needed values.

#### Clients

The launcpad provisioner natively supports 2 plugins, which it creates by
downloading the client bundle.

1. mtt_docker client : which is an extension of the docker python sdk
2. mtt_kubernetes client : which can get you kubernetes API clients

Any other request for a plugin will be passed to the backend,

## Config

### Variations

The mtt offers a variation concept, where common mirantis presets for
testing clusters is created as batches of config, which can be loaded as presets
based on values in the config.load('mtt').

The variation presets are meant to simplify configuration of systems by putting
complexity in mtt-mirantis, and using `variables` config to provide simple
values that override settings.
The variations should be usable with next to no overrides, but the overrides
provide the flexibility.

The following values are available:

Variation : a preset master which is usually just a comprehensive configuration
    for a terarform chart, with better parametrization for configuring.

    The LTC variation is an attempt to mix terraform/launchpad and some good
    presets.

Release : small preset options which overload `variables` for different MKE/MSR
   /MCR versions and sources .

Platform : small preset options which overload `variables` for different server
   OS versions that should be used in the cluster.

Cluster : small preset options which overload `variables` for different cluster
   sizes and MKE/MSR combinations.

To consumer variations, populate an `mtt` config with variation/release
/platform/cluster ids, and then ask mtt to process them and it will load
all the needed config to provide a valid provisioner.

## Terraform

Mirantis uses a number of terraform charts with mtt.  These are provided with
the mtt module to give access.
Additionally, there is some `mtt` configuration meant to give easy path
access to the terraform plans/charts.

Look in` mtt/config/mtt` for the values.

two useful charts are:

1. example : the example terraform aws chart that is referenced in the launchpad
   documentation.
2. prodeng : a chart that the testing team uses.  It is complex but comprehensive
   with settings for a lot of overrides.
