# Provisioner

Provisioners are MTT plugins that are responsible for managing the state of the
testing resources.  Typicall a provisioner is used to bring up a testing cluster
or to alter a testing cluster based on a change of configuration.

## Interface

### Cluster Management

#### Apply

The apply method is expected to bring all testing resources to the state described
by the provisioner configuration

#### Destroy

The destroy method is expected to wipe out all resources created by the provisioner

### Cluster interaction

#### Client

Provide a client from the provisioned resources 
