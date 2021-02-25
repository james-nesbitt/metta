# Workloads

Workload plugins can apply workloads to a cluster if given the right client.

A workload has some internally discovered configuration which tells it what to
do, and it can apply that workload to a client of a known type.

Typically a workload is given access to a provisioner from which it can ask
for a client, and then it uses the client internally

## Usage

Workloads are METTA plugins.  You can ask metta.plugin for a plugin instance but
there is a way to leverage config to create a dict of workloads. Look in the
metta.__init__.py for more information.

When you have a workload plugin, it will need clients in order to apply a load.
Typically a workload plugin will accept a provisioner when it executes, as it
can ask the provisioner directly for the plugins that it needs.

## example

an example would be a kubernetes yaml spec workload.  Such a plugin would ask
a client for the kubernetes client, and then it would ask the client for
resources to apply the yaml to.
