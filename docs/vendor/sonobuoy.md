# METTa Sonobuoy integration

The contrib sonobuoy package contains a workload plugin which will run sonobuoy
tests against an existing cluster.

The implementation is based around python subprocess commands which run kubectl
and sonobuoy on the command line.

## Requirements

The Sonobuoy workload plugin currently requires a kubeapi_client but only to
provide a KUBECONFIG file.  We should be able to provide alternate options for
providing kubectl access.

For `os.subprocess` both sonobuoy and kubectl are needed. Consider using the
binhelper utlity plugin for ensuring those are avaialble.
