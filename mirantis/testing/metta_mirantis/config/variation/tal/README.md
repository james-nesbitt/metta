# T.A.L.

An metta conmfiguration variation which leverages three provsioners:
1. Terraform : metta_terraform : Provision resources with terraform
2. Ansible : metta_ansible : Modify provisioned terraform resources
3. Launchpad : metta_launchpad : Ask launchpad to install products onto the
   terraform resources.

An metta configuration set which creates three provisioners.

## Usage

To use this variation in your metta environment you need only two things:

1. Your environment needs to be bootstrapped with `metta_mirantis_presets` which
   tells metta to include the `mirantis/testing/metta_mirantis/presets.py` code
   that looks for and includes config presets.
2. You need a config source that sets this preset up as the `variation`.

For #2, having a config file such as:

metta.yml:
```
presets:
  variation: lat
```

## Variation components

The following metta componetns are included in this variation:
## Fixtures

The following fixtures are included:

1. Terraform provisioner configured using any `terraform.yml`
2. Ansible provisioner configured using config from `fixtures.yml`
3. Launchpad provisioner configured using config from `fixtures.yml` which
   instructs the provisioner to pull an output with `instance_id: mke_cluster`

## Configuration

### Fixtures

The metta configuration uses `fixtures` to indicate the fixture list, and mainly
configures fixtures in that file directly.  The Terraform provisioner is an
exception, as its config is pretty long - so it gets its own file.

### Variables

The plugin configuration for Terraform relies heavily on injection from the
`variables.yml` file.  This means that it is easy to override in your config
or by combining with other presets.
