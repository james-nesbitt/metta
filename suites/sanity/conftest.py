import pytest
import logging

from uctt import new_environment
from uctt.plugin import Type


logger = logging.getLogger('mtt ltc demo pytest')

ENVIRONMENT_NAME = 'sanity'
""" What to call our UCTT Environment """
PROVISIONER_INSTANCE_ID = "{}-provisioner".format(ENVIRONMENT_NAME)

""" Define our fixtures """


@pytest.fixture(scope='session')
def environment():
    """ Create and return the common environment. """
    environment = new_environment(name=ENVIRONMENT_NAME, additional_uctt_bootstraps=[
        'uctt_docker',
        'uctt_kubernetes',
        'uctt_terraform',
        'mtt',
        'mtt_launchpad'
    ])
    # This does a lot of magic, potentially too much.  We use this because we
    # found that we had the same configerus building approach on a lot of test
    # suites, so we put it all in a common place.

    # Tell UCTT to load config from the fixtures.yml file, and use its contents
    # to define what initial fixtures we want.
    # We will want at least to define a provisioner.
    environment.add_fixtures_from_config()

    return environment


@pytest.fixture(scope='session')
def provisioner(environment):
    """ Retrieve a provisioner object

    The 'ltc' key matches the provisioner name as defined in the fixtures
    file.  We could just use the first Provisioner plugin, but this is more
    explicit.

    Raises:
    -------

    If this raises a KeyError then we are probably using the wrong name.

    """
    provisioner = environment.fixtures.get_fixture(
        type=Type.PROVISIONER, instance_id='ltc')
    return provisioner


@pytest.fixture(scope='session')
def provisioner_up(provisioner):
    """ get the provisioner but start the provisioner before returning

    This is preferable to the raw provisioner in cases where you want a running
    cluster so that the cluster startup cost does not get reflected in the
    first test case which uses the fixture.  Also it can tear itself down

    You can still use provisioner.apply() update the resources if the provisioner
    can handle it.
    """

    # the provisioner has its own config object, which we will use to make
    # some project decisions.  We could pull in the environment object and
    # use its config, but this is simpler.
    conf = provisioner.environment.config.load("config")
    """ somewhat equivalent to reading ./config/config.yml """

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

    if conf.get("keep-on-finish", exception_if_missing=False):
        logger.info("Leaving test infrastructure in place on shutdown")
    else:
        try:
            logger.info(
                "Stopping the test cluster using the provisioner as directed by config")
            provisioner.destroy()
        except Exception as e:
            logger.error("Provisioner failed to stop: %s", e)
            raise e
