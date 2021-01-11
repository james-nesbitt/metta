# MTT advanced terraform/launchpad leveraging mtt_common

MTT demo that uses Launchpad and Terraform for provisioning, and leveraging the
mtt_common module/package for shared/common resources such as the teraform plan.

The idea is that config here will point to a terraform plan in mtt common, with
local conig override.
The result is a fair amount of dymanic/templated config, but this module is
kept free of terraform plan info, and can focus on straight testing.

The config sources include:
1. local ./config path
2. ./ path used for building file paths for things like the launchpad yml
3. mtt_common config and root (which are added by the mtt_common bootstrapper)
4. user globals
5. defaults for mtt

The config labels that matter are:

1. "mtt" is used to bootstrap the mtt_common module
2. "config" is used for some global config that is used for templating in the
    other sources
3. "provisioner" tells mtt that launchpad will be the provisioner
4. "launchpad" configures mtt_launchpad including selecting terraform as the
    backend provisioner
5. "terraform" configures mtt_terraform to user plans from mtt_common

you can look at the mtt_common/config to see how plans in that module are
configured as variables so that templating in this module is easier.

## Running this demo

This demo requires:

1. "mtt" python distribution is installed,
2. AWS config is available,
3. and that the required binary commands can be found:
    i. terraform
    ii. launchpad

MTT can be installed using various methods
```
# pip global install (NOT YET REGISTERED)
pip install mtt

# OR pip install from a cloned/downloaded mtt
pip install -e path/to/mtt
```

now in this demo folder
```
export AWS_SECRET_ACCESS_KEY="XXXXXXXXXXXXXXXXXXX"
export AWS_SESSION_TOKEN="YYYYYYYYYYYYYYYYYYYYYYY"

pytest
```

## Current status

The test suite runs, creating cluster infra using terraform, and installing
using launchpad.

1. the first test suite just does some sanity testing on the config object
2. the clients test suite retrieves docker and k8s clients and confirms that
    they point to the cluster.
