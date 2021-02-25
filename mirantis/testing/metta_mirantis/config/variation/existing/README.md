# Existing cluster

Test against existing cluster resources, that still need Mirantis products
installed.

## Usage

You need to do 3 things to use this variation:

1. Bootstrap your environment with `mettat_mirantis_presets` to tell metta to
   look for preset configuration in `metta.yml`;
2. Include a `metta.yml` in your project config which indicates that the
   variation should be `existing`;
3. This variation requires a `variables.yml` override for `launchpad_source_path`
   which should contain a path to the launchpad config file.

## Configuration

Only two configuration labels are used here:

1. `fixtures.yml` defines the two fixtures which are used
2. `variables.yml` defines variables which are injected into the fixtures file.

You should be able to override just the variables file in any test suite project.

## Fixtures

2 fixtures are used:

1. An dummy output fixtures `mke_cluster` whic will pipe the contents of a yaml
   file to the launchpad provisioner to provide it with its launchpad config.

2. A launchpad provisioner which will pull its config form the dummy output and
   install Mirantis products onto the cluster.  The provisioner will then
   provide clients that can connect to the cluster.
