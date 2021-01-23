# Tester guide

## Basics

The primary approach to testing should be to prepare configuration in your test
suite, and consumer variations of that configuration per test-case by building
config objects that meet the needs of each case, and using that to build the
other needed objects.

A typical case workflow itsef:

1. Configure a config object
2. use the config object to create a provisioner and workload instances
3. make the provisioner start any needed resources for testing
4. use the workload plugins to apply any load or resources to your cluster
5. test
6. use the provisoner to tear down any created resources

In general, if you build your config object right, the rest is straight forward
and not a lot of code.

## with test frameworks

MTT was developed to be used with test frameworks such as pytest.  The components
match injection patterns like pytest's fixtures with ease, and external modules
can inject plugin registration with simple imports at bootstrap time.

See `./pytest.md` for more information
