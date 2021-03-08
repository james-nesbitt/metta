# Mirantis Metta suites

Common testing suites that Mirantis uses for system testing.

## Usage

### Python / PyTest

Note the following pip options:

1. you can install metta from pypi for install from the repo root
2. you can install pytest manually or use the miranits-metta-suites package
3. you can use the `in-docker` shell script to run in a container that has
   the dependent tools installed such as helm, terraform and launchpad.

### Jenkins

There is a provided Jenkinsfile.  The Jenkinsfile is designed to be run from
the metta project root.  First it installs the mirantis-metta pip package from
the repo root, then it installs the suite dependencies, from this folder.

Then it lets you pick tests to run.

## Suites

### Sanity


### Upgrade


### Docker / Kubernetes / Helm
