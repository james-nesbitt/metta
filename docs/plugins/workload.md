# Workloads

Workload plugins can apply workloads to a cluster if given the right client.

A workload has some internally discovered configuration which tells it what to
do, and it can apply that workload to a client of a known type.

Typically a workload is given access to a provisioner from which it can ask
for a client, and then it uses the client internally

## example

an example would be a kubernetes yaml spec workload.  Such a plugin would ask
a client for the kubernetes client, and then it would ask the client for resources
to apply the yaml to.
