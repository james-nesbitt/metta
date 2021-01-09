# Mirantis testing toolbox

Test a Mirantis product cluster.

The tooling primarily focuses on getting a test target cluster up an running,
and providing access to the cluster for tooling.

The first goal was to provide a pytest interface, so the tooling is based around
providing access as would be consumed using pytest fixtures.
