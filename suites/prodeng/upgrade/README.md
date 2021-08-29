# Launchpad-Terraform Complete

This test suite demonstrates running the recommended Mirantis approach of
using Launchpad and Terraform to run provision a cluster and provide clients.

## Config

The configuration is somewhat complex but has good separation with the majority
being derived directly from the metta code.

The terraform plans are all in metta_mirantis, as is a lot of the config.
See metta_terraform for the plans and metta_mirantis/config for the more
complex config.
Note that we leverage the metta 'variation' and 'release' concepts which
allow us to set simple values in our `config/metta` file which tell
that module to add more config sources from the `metta_mirantis/config` path.
@see `metta/__init__.py:config_interpret_metta()`.

We also allow metta_common to add some common config sources, such as its own
sane defaults from `metta_common/config` and some allowed overrides from you own
user folder.

### Presets

The nature of the tal config layout allows us to focus overriding its config
with values by including other preset or in our own `config/variables` config.

@see `metta_mirantis/config/variation/tal`.

### Fixtures

3 Provisioners fixtures are included in this metta implementation.  These are
included in the lat variation preset, so can be found in the fixtures.yml file
in `mirantis/testing/metta_mirantis/config/variation/lat`.

1. Terraform : Will create cluster resources for testing against;
2. Ansible : Will modify cluster resources
3. Launchpad : Will install Mirantis products onto the cluster

In ./config/fixtures.yml 2 Workloads are configured to run sanity tests against
the provisioned cluster:

1. sanity_docker_run : A docker `hello-world` run to prove that the docker
   implementation can pull images, create and start containers;
2. sanity_kubernetes_deployment : an nginx workload that will run in the
   background.



## Usage

### Pytest

The setup should be good to go if you get the requirements installed.  You
should be able to run pytest as normal.

### Cli

There is a python setuptools entrypoint `metta` which you can use to interact
with the metta plugins directly for debugging and management.
