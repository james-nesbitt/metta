# Mirantis testing toolbox

Test a Mirantis product cluster.

The tooling primarily focuses on getting a test target cluster up an running,
and providing access to the cluster for tooling.

The first goal was to provide a pytest interface, so the tooling is based around
providing access as would be consumed using pytest fixtures.

## Status

this has been written by one and tested using some generic usecases.  It is not
likely stable, but it is likely to be interesting.

## How to use this

Check out ./demos for some early examples

## TODO

1. improve this README
2. start on ./docs
3. start on "workloads"
