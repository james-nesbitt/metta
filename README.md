# Mirantis Testing Toolbox

The Mirantis Testing tooblox cluster management framework for creating test
harnesses to test against.

## Dependencies

### Configurus

Configerus is heavily leveraged for dynamic and abstracted configuration.

Primarily two aspects are used:

1. centralized configuration in order to separate plugins which need config from
   the configuration that they need; this allows simpler management and overrides.

2. Configerus source overrides are used to implement a preset system where
   configuration sources are included based on what preset keys are requested.
   This allows easy switching of cluster platforms, cluster size and mirantis
   product versions.

## Getting started

see our ./docs section for better running instructions

## Contributing

Feel free to open issues and PRs directly.
