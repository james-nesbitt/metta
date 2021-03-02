# Upgrade Test

This test suite performs a platform upgrade to test stability of running
workloads across upgrades

## Environments

The Metta design for the upgrade tests is to use to environments, both configured
to be almost identical, with only a metta_mirantis preset difference for
`release`.
Each environment is a full declarative state (could be provisioned on its own)
but because they are very similar, and both terraform and launchpad can detect
that, the provisioner of the second start from the first performs just an upgrade.

### Before

This is meant to be the first state.  Choose an earlier `release`

### After

This is the finals state.  Choose a later `release`.  Probably try to avoid any
metadata changes that would alter the names or settings of any terraform assets
as that would cause terraform to tear down and recreate those assets.

## Config

The project root is denoted by the lowest level `metta.yml` which tells metta
to look in the ./config path for config.  The suite relies primarily on ./config
for its baseline, with each environment  adding either ./config/after or
./config/before for its case.

The suite leverages the metta_mirantis `presets` to include common terraform,
and launchpad configuration.  This means that each environment need only declare
preset values in a `metta_mirantis.yml` file.  There is a common file, and each
environment includes overrides in their folder.

### Presets

#### Variation: tal

The basis of the suite is the `tal` variation, which includes base `fixtures`
and `terraform` configuration pulling base configuration variables into a
`variables.yml` file.  You can override those variables in the ./config
yourself.
Keep in mind that those variables can be used for naming of assets, so changing
them might lose track of created resources.

@see `metta_mirantis/config/variation/tal`.

#### cluster: poc

A small cluster.  Feel free to choose another, but don't vary between the
environments

@see `metta_mirantis/config/cluster/poc`.

#### platform: public/ubuntu/20.04

Use a plublic AMI for ubuntu-20.04 (Focal) for nodes

@see `metta_mirantis/config/platform/public/ubuntu/20.04`.

### Fixtures

3 Provisioners fixtures are included in this metta implementation.  These are
included in the lat variation preset, so can be found in the fixtures.yml file
in `mirantis/testing/metta_mirantis/config/variation/lat`.

1. Terraform : Will create cluster resources for testing against;
2. Ansible : Will modify cluster resources
3. Launchpad : Will install Mirantis products onto the cluster

In ./config/fixtures.yml a Kubernetes deployment workload is defined using a
common nginx server workload.

It would be interesting to use a different deployment that could provide more
value.

The Terraform provisioner may include several Output fixtures, if it is already
provisioned.
The Launchpad provisioner will include docker-py and kubernetes clients if
already provisioned.

## Usage

### Pytest

The setup should be good to go if you get the requirements installed.  You
should be able to run pytest as normal.

You will need to have the metta package, and pytest (and pytest-order) installed
to run this pytest suite.

You will need some AWS credentials in scope, then just run the following in
the project root:

```
$/> pytest -s
```

(you can use the `python -m pytest -s` approach as well.)

You can see the approach to fixtures in `conftest.py`.  There we have two
provisioner fixtures used to retrieve the metta environment objects. Each
fixture factory will first check to see if the environment has been provisioned,
and if not it will do so.

You will need to make sure that you don't run any tests using the "before"
environment after the "after" environment, as using the latter will run the
after provisioning.

### Cli

You will need the metta package installed, and AWS credentials will be needed
for the terraform provisioning step.

There is a python setuptools entrypoint `metta` which you can use to interact
with the metta plugins directly for debugging and management. This should have
been installed when you installed metta itself.

This executable will recognize your environment if it finds a metta.yml file and
will allow you to inspect the metta configuration, and environment in detail in
order to debug any errors or configuration changes.
