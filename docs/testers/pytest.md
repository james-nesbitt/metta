# Using with pytest

It is common to use metta with pytest by injecting config provisioner and workload
plugins as fixtures.

If you are running tests using a single long running cluster then you can inject
a provisioner fixture that has already started the cluster resources.
Multiple provisioners can be used if you want to separate resources and run
tests in parallel.

## Environments

At least one environment will be need for your PyTest implementation.

You can create that environment as a pytest fixture, but keep in mind that if
you want to use the UTCC cli, you will need a `metta.py` module also knows how
to build the environment.
A Common approach is to create your environment in the `metta.py` module in your
pytest root, and then import that into your conftest and then retrieve the
environment using `metta.environment.get_environment()`.

The easiest way to get METTA fixtures into your environment is to have a
`fixtures.yml` file in a config folder that defines needed fixtures.

## PyTest fixtures

Typical tests will need access to METTA fixtures in order to interact with
test infrastructure.
As the environment also contains config, tests will often need access to it as
a pytest fixture.

A good approach is to use pytest fixtures to wrap individual METTA fixtures
such as the provisioners or workloads.

METTA plugins fit well into pytest fixture scenaris they are either constructed
ready to use, or can be dynamically configured on the fly.

### provisioner fixtures

Provisioners are easy to get if you have your config object.

Just use something like:

```
@pytest.fixture(scope='session')
def provisioner(environment):
    """ Retrieve a provisioner object ""

    """
    return environment.get_plugin(type=metta.plugin.Type.OUTPUT, instance_id='my_provisioner')
```

This will give a non-provisioned provisioner that you can bring as needed.

If you want to keep provisioning times out of your test functions, then consider
injecting a provisioner that has already provisoned your cluster.

```
@pytest.fixture(scope='session')
def provisioner_up(provisioner):
    """ get the provisioner but start the provisioner before returning

    This is preferable to the raw provisioner in cases where you want a running
    cluster so that the cluster startup cost does not get reflected in the
    first test case which uses the fixture.  Also it can tear itself down

    You can still use provisioner.apply() update the resources if the provisioner
    can handle it.
    """
    logger.info("Running METTA provisioner up()")


    try:
        logger.info("Preparing the testing cluster using the provisioner")
        provisioner.prepare()
    except Exception as e:
        logger.error("Provisioner failed to init: %s", e)
        raise e
    try:
        logger.info("Starting up the testing cluster using the provisioner")
        provisioner.apply()
    except Exception as e:
        logger.error("Provisioner failed to start: %s", e)
        raise e

    yield provisioner

      try:
          logger.info("Stopping the test cluster using the provisioner as directed by config")
          provisioner.destroy()
      except Exception as e:
          logger.error("Provisioner failed to stop: %s", e)
          raise e
```

Often systems use multiple provisioners.  Such systems can manage the order of
operations to get a cluster running, or in simpler scenarios there is a `combo`
provisioner which will group provisioners together into a single interface.

### Clients

Any test can ask for the environment (or a provisioner plugin) for a client plugin
and use it directly.  Client plugins are quite diverse in behaviour, so their
use is particular to the need.

### Workloads

Workloads can be use to standardize workloads applied to a cluster.,  They need
to be given access to clients, and tehn can apply or destroy a workload to a system
