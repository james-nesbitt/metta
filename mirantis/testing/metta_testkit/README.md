# METTA testkit

Mirantis has a tool called testkit which gets used to create an manage clusters
with installed Mirantis products.  This is used primarily as a testing and
developer tool.

This Python package contains Metta integration for the testkit tooling.

This package provides the following plugins:

1. a provisioner plugin which can be used to create and manage clusters.
2. a cli plugin which allows interaction with the testkit integrations.

These plugins rely on a separate module class which can be used to interact
with the testkit tool, via python subprocess; this requires that you have
installed testkit in the python environment.
