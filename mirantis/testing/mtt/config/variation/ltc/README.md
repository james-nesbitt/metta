# ltc

An MTT configuration set which combines a launchpad, terraform and common config
setup.

## Usage

You should look at the `mtt:__init__.py` for how variations and
releases can be used to get this activated

Basically you can just use a `mtt` config (file or dict) that should
contain a `variation` key with value ltc, and then run the

## Plugins

mtt_common:
    configsource: dict
    configsource: path

mtt:
    provisioner: launchpad

mtt_terraform:
    provisioner: terraform

## Configuration

Focus has been made to parametrize all config to be based on `variables` config
source with sane defaults where possible.
Of not as well is the leveraging of plans configuration in mtt.

### MTT_Mirantis

We override the variation to LTC here, which tell mtt to include
`mtt/config/variation/ltc`.  That ltc variation has all of the complex
code for launchpad and terraform, with the variable file allowing easier
parameterization.

The mtt config in the `mtt/config` path is also important as it
provides template variables which give the paths to different terraform plans
so that you don't have to build your own.

### Variables

A lot of the changeable config has been kept here to be parameterized to the
other files.  This makes overrides more linear and easier to read.

### Provisioner

We only use this to tell MTT that our provisioner will be launchpad

### Launchpad

We tell launchpad that we will use terraform as our backend.  We don't provide
any config directly to the terraform plugin as it reads its own terraform config
so we can just directly modify that

### Terraform

We configure the terraform plugin to use a plan by referencing a plan path
defined in mtt
