# Provisioner

Provisioners are METTA plugins that are responsible for managing the state of the
testing resources.  Typicall a provisioner is used to bring up a testing cluster
or to alter a testing cluster based on a change of configuration.

## Usage

you can get a provisioner plugin by passing a configerus.config.Config object
to the METTA provisioner constructor.

The constructor will build a provisioner by loading a config label (the default
label is `provisioner`) and asking first for a `plugin_id`. When a plugin_id is
found, that plugin is loaded and passed the config object.
From there the plugin itself is returned and it can be used directly to
provisioner a cluster.

The plugin itself tends to read config in its own way, so you'll want to check
the conventions of the plugin itself to know what config will be needed.

### Cluster Management

#### Prepare

Prepare the plugin for running, loading config, applying any changes and perhaps
preparing external resources for running.

We don't load config in the plugin constructor so that we can keep the object
lean until we need action.

Terraform uses this to run the terraform init command.

#### Apply

The apply method is expected to bring all testing resources to the state described
by the provisioner configuration

#### Destroy

The destroy method is expected to wipe out all resources created by the provisioner

### Cluster interaction

#### Output

Get a named return object or string.

This is modelled after terraform's ability to return data, which couples nicely
into code that can interpret and read.

If you format your outputs the right way then metta will actually be able to
natively construct a dict of clients and workloads directly.

#### Client

Provide a client from the provisioned resources
