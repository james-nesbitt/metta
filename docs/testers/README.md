# Tester guide

## Basics

The primary approach to testing should be to prepare configuration in your test
suite, and consumer variations of that configuration per test-case by building
config objects that meet the needs of each case, and using that to build the
other needed objects.

A typical case workflow itsef:

1. Include in your test suite, some python code which creates a new environment
2. Add some config to your project that tells METTA what fixtures you want
3. Use Provisioner clusters to manage your cluster
4. test, ask the Environment/Provisioners for clients if you need access to the cluster
5. use the Workloads to apply any load or resources to your cluster
6. use the Provisoners to tear down any created resources

In general, if you build your config object right, the rest is straight forward
and not a lot of code.

## with test frameworks

METTA was developed to be used with test frameworks such as pytest.  The components
match injection patterns like pytest's fixtures with ease, and external modules
can inject plugin registration with simple imports at bootstrap time.

See `./pytest.md` for more information
