# Terraform Launchpad and Ansible

Here is an in-line, self-encapsulated mtt demo that uses the 3-provisioner
combination of:
1. terraform creates initial infrastructure
2. ansible modifies that infrastructure
3. launchpad installs the products for testing on the infrastructure

Then tests can be executed on those environments

## Environment (UCTT)

A single UCTT environment is used.  It is defined in the ucct.py file, which is
included in the pytest conftest.py.  The UCTTC cli program automatically
discovers the file.

The environment is configured in the ./uctt.py file, which is included by pytest
and by the ucttc cli.

The environment includes all MTT defaults:

1. Some user defaults could be put into ~/.config/mtt/ config files
2. Common MTT config is included, including a /config folder and some constants
3. fixtures are loaded from any fixtures.yml files

Any code can access the environment by name, and access the fixtures list as
needed.

An additional config folder is added in uctt.py.  The ./config/release/XXXX path
is included as a config source. This path is used to configure launchpad package
versions for install.  These could be inlined, but it shows off the configerus
overriding features.

## Config

1. fixtures.yml: used to define a starting list of fixtures
2. teraform.yml: terraform configuration could be kept in the fixtures.yml, but
   it get's pretty long, so it is kept in its own file.
3. version.yml: contains some values for install versions which are directly
   pulled into the terraform yaml.

The config/release/XXXXX path overrides some `version` config

1. "{paths:project}" is used to string substitate the root path to this project
  into some configurtion values.  This is needed in order to allow relative
  values in other places in the config.  Withoout this, you would not be able
  to run pytest or ucttc in a subfolder of your code.
  The value for this config is set to the project root, as identified by the
  existence of any of the files: ucct.py, conftest.py, pytest.ini
2. "{id}" : a string that is used across the place as a prefix for files. This
  could allow one terraform chart to be used for multiple clusters, but in
  general is just used for labeling

## Fixtures

### Provisioners

#### Terraform

This is the most import provisioner as it creates infra, and also outputs the
yaml configuration for launchpad.

Inlined in the folder is a terraform root module in the `tf_prodeng_plan` path.
The configuration is all in terraform.yml which is loaded as a configerus source.

Note that there are some important configerus templating implementations.

The terraform plan produces and important `output` "mke_cluster" which the
launchpad provisioner will consume when it runs.

#### Ansible

This is currently a stub provisioner, awaiting some functionality ideas.

#### Launchpad

Will install the suite of products onto the terraform cluster, pulling its
yaml directly from that provisioner.

It will create two clients as long as it has a valid yaml file, and can download
client bundles.

### Workloads

#### sanity_docker_run

A docker run workload that runs hello-world.  Give it the launchpad provisioner
for fixture source.

#### sanity_k8s_deployment

A kubernetes deployment workload that runs nginx in a pod.  It can tear down
the deployment.

## Usage

### Pytest

The setup should be good to go if you get the requirements installed.  You
should be able to run pytest as normal.

### Cli

Yiou
