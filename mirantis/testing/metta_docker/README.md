# metta Docker package

## metta Plugins

### Client

The metta_docker plugin is actually just a py docker client wrapper.  You can
treat it like that client.

@NOTE should we switch to https://pypi.org/project/python-on-whales/ ? It
   requires that a docker cli is installed

### Run Workload

The Run workload take a docker client plugin and runs a docker container based
on configuration that provides things like image name.
