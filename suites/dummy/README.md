# Dummy metta

This is a pytest test suite which can be used to test overall metta workflows
without any network/cluster resources being used.

The test suite is centered around the metta_dummy plugins, which are usable for
mocking and debugging.

Use this if you are curious about some core plumbing and want to see what happens
when you change things.  It is fast and breakign it has no real impact.

## Environment

A single environment called `dummy` is defined in `./config/environemnt.yml`.  
Fixtures are loaded directly from `fixtures.yml` (as directed in the env config)

## Fixtures

This suite creates fixtures only for the purpose of running tests, and is not
trying to make fixtures that make sense for all testing scenarios.  That said
it does try to run some standard workflow to confirm that the metta plumbing
works.

## Plugins

Dummy plugins meet the interface expectations of their implementation but really
they do nothing other than return a configured set of fixtures themselves and
run logging events as needed.

In general, the end result of the fixtures is that a fixtures.get_plugin() call
will be run, and output plugins will be checked for proper output.

It should be clear that you can use dummy plugins to mock any other plugin by
programming it with the required fixtures list.

## Usage

### Pytest

The setup should be good to go if you get the requirements installed.  You
should be able to run pytest as normal.

You will need to have the metta package, and pytest (and pytest-order) installed
to run this pytest suite.

You will need some AWS credentials in scope, then just run the following in
the project root:

```
$/> pytest -s
```

(you can use the `python -m pytest -s` approach as well.)

You can see the approach to fixtures in `conftest.py`.  There we have two
provisioner fixtures used to retrieve the metta environment objects. Each
fixture factory will first check to see if the environment has been provisioned,
and if not it will do so.

You will need to make sure that you don't run any tests using the "before"
environment after the "after" environment, as using the latter will run the
after provisioning.

### Cli

You will need the metta package installed, and AWS credentials will be needed
for the terraform provisioning step.

There is a python setuptools entrypoint `metta` which you can use to interact
with the metta plugins directly for debugging and management. This should have
been installed when you installed metta itself.

This executable will recognize your environment if it finds a metta.yml file and
will allow you to inspect the metta configuration, and environment in detail in
