# Using with pytest

It is common to use mtt with pytest by injecting config provisioner and workload
plugins as fixtures.

If you are running tests using a single long running cluster then you can inject
a provisioner fixture that has already started the cluster resources.
Multiple provisioners can be used if you want to separate resources and run
tests in parallel.

## Config fixtures

A comprehensive config structure could be:

```
@pytest.fixture(scope='session')
def config():
    """

    Create a config object.

    We add sources for:
    - our own ./config
    - some dynamic overrides
    - we let mtt_common add some common paths
    - we let mtt_mirantis interpet variation and release from its config

    """

    config = mtt.new_config()
    # Add our ./config path as a config source
    config.add_source(mtt_common.MTT_PLUGIN_ID_CONFIGSOURCE_PATH, 'project_config').set_path(os.path.join(DIR, 'config'))
    # Add some dymanic values for config
    config.add_source(mtt_common.MTT_PLUGIN_ID_CONFIGSOURCE_DICT, 'project_dynamic').set_data({
        "user": {
            "id": getpass.getuser() # override user id with a host value
        },
        "global": {
            "datetime": datetime.now(), # use a single datetime across all checks
        },
        config.paths_label(): { # special config label for file paths, usually just 'paths'
            "project": DIR  # you can use 'paths:project' in config to substitute this path
        }
    })

    # adds user and mtt_common defaults
    mtt_common.add_common_config(config)
    # let mtt_mirantis interpret stuff from the mtt_mirantis config
    mtt_mirantis.config_interpret_mtt_mirantis(config)
    # of primary value is that mtt_mirantis can interpret ./config/mtt_mirantis
    # to determing a cluster, variation and release, which adds more config from
    # that module.

    return config
```

This contains a config object which reads from the `./config` folder, as well as
paths like `~/config/mtt/`.
It is also configured to interpret config for the `mtt_mirantis` label and load
more config from `mtt_mirantis/config`
Some additional dynamic values have been added so that you can inject a username
and a fixed datetime for consistent datetime labelling.

The real mtt advantage is getting strong control over config, and then letting
mtt do the rest by relying on that configuration.
The actual config demands of the plugins may take some learning, but using things
like the mtt presets should help a lot.

## provisioner fixtures

Provisioners are easy to get if you have your config object.

Just use something like:

```
@pytest.fixture(scope='session')
def provisioner(config):
    """ Retrieve a provisioner object

    we only use one provisioned cluster in this test suite
    (but we still give it an arbitraty name)

    Use this if your test-cases want unprovisioned resources, but then they
    need to manage startup and teardown themselves.

    @see provisioner_up

    """
    return mtt.new_provisioner_from_config(config, 'my_provisioner')
```

This will give a non-provisioned provisioner that you can bring as needed.

If you want to keep provisioning times out of your test functions, then consider
injecting a provisioner that has already provisoned your cluster.

```
@pytest.fixture(scope='session')
def provisioner_up(config, provisioner):
    """ get the provisioner but start the provisioner before returning

    This is preferable to the raw provisioner in cases where you want a running
    cluster so that the cluster startup cost does not get reflected in the
    first test case which uses the fixture.  Also it can tear itself down

    You can still use provisioner.apply() update the resources if the provisioner
    can handle it.
    """
    logger.info("Running MTT provisioner up()")

    conf = config.load("config")

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

    if conf.get("options.destroy-on-finish", exception_if_missing=False):
        try:
            logger.info("Stopping the test cluster using the provisioner as directed by config")
            provisioner.destroy()
        except Exception as e:
            logger.error("Provisioner failed to stop: %s", e)
            raise e
    else:
        logger.info("Leaving test infrastructure in place on shutdown")
```
