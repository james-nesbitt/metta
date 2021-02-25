# Terraform contrib package

METTA Plugins for itneracting with infra using terraform.

## Provisioner plugin

This is the primary plugin for usage.  It allows typical terraform operations
such as init (using `prepare()]`) and apply/destroy.

The plugin also produces dict/text output plugins from any output declared at
the root module.

### Configuration

This plugin uses configerus for configuration.  The constructor takes a configerus
label and key as a base for config.

By default it looks in the root of `terraform`, which means that you can put all
of the needed config into a `terraform.yml` file in a config source path.

The plugin includes a jsonschema definition for its config.
