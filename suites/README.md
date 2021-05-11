# Mirantis Metta suites

Common testing suites that Mirantis uses for system testing.

## Usage

Each test suite is its own python package, and is implemented using its own
tooling.  That said, most of the suites work the same way.

1. Each suite is a package, which needs to be installed using pip in order to
   apply prerequisites.
2. Each suite is written using pytest, and can be run using pytest directly.
3. Each suite has a .pytest.sh shell script for conformant pytest plugin 
   behaviour.

### Python / PyTest

```
$/> pip install .
$/> ./pytest.sh
```

### Jenkins

Each suite has a Jenkinsfile.

The Jenkinsfile is designed to be run from the metta project root.  This is
because Jenkins always starts from the git repo.

## Suites

### Sanity

A small environment creation and tear-down test suite for MCR/MKE/MSR

### Upgrade

An upgrade test for MCR/MKE/MSR which allow a single stage upgrade from
any version combination to any other version combination

### Docker / Kubernetes / Helm (client)

A metta client test, which will test docker/k8s/helm and exec (ssh) 
functionality on a cluster.

### CNCF

Run the CNCF conformance test against a cluster

### NPods

Test that a certain number of pods can function on an MKE k8s cluster.

### Cross-Version

Cross version testing mixing different versions of the products.
