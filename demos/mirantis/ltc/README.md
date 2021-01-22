# Launchpad-Terraform Complete

This test suite demonstrates running the recommended Mirantis approach of
using Launchpad and Terraform to run provision a cluster and provide clients.

## Config

The configuration is somewhat complex but has good separation with the majority
being derived directly from the mtt_mirantis code.

The terraform plans are all in mtt_mirantis, as is a lot of the config.
See mtt_mirantis/terraform for the plans and mtt_common/config for the more
complex config.
Note that we leverage the mtt_mirantis 'variation' and 'release' concepts which
allow us to set simple values in our `config/mtt_mirantis` file which tell
that module to add more config sources from the `mtt_mirantis/config` path.
@see `mtt_mirantis/__init__.py:config_interpret_mtt_mirantis()`.

We also allow mtt_common to add some common config sources, such as its own
sane defaults from `mtt_common/config` and some allowed overrides from you own
user folder.

The nature of the ltc config layout allows us to focus overriding its config
with values primarily in our own `config/variables` config.
@see `mtt_mirantis/config/variation/ltc`.

### Launchpad / Terraform

Launchpad from `mtt_mirantis` is configured to use terraform as its backend,
and terraform reads from its own config.  the `ltc` variation has most of that
complexity.
The `mtt_mirantis` config also contains some configuration for terraform plans
that we at Mirantis use.  That config is there to allow eay access to the plan
paths without having to build your own complex strings.
@see `mtt_mirantis/config/mtt_mirantis`

## Usage

The setup should be good to go if you get the requirements installed.  You
should be able to run pytest as normal.
