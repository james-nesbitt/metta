# Mirantis Testing Toolbox

A UCTT extension that includes mirantis specific plugins for launchpad and some
streamlining for using UCTT in pytest based testing of Mirantis products.

## Dependencies

### Configurus

Configerus is heavily leveraged for dynamic and abstracted configuration.

Primarily two aspects are used:

1. centralized configuration in order to separate plugins which need config from
   the configuration that they need; this allows simpler management and overrides.

2. Configurus source overrides are used to implement a preset system where
   configuration sources are included based on what preset keys are requested.
   This allows easy switching of cluster platforms, cluster size and mirantis
   product versions.

### UCTT

UCTT is used as a testing infrastructure management platform, and its plugins are
the basis of the mtt implementation.  MTT also provides some additional plugins.

UCTT environments are expected to the basis of your MTT testing suites, with
MTT bootstrapping and configuration patterns used to simplify cluster management.

## Getting started

see our ./docs section for better running instructions

## Contributing

Feel free to open issues and PRs directly.
