"""

PYTest Integrations

"""
import logging
import pytest

import mirantis.testing.mtt as mtt

logger = logging.getLogger('mtt.pytest.common')

MTT_COMMON_CONFIG_LABEL = 'common'
""" configerus config label used to configure common fixtures """
MTT_COMMON_CONFIG_KEY_KEEPONFINISH = 'keep-on-finish'
""" configerus config key that tells us to keep provisioned resources """

""" Define our fixtures """


@pytest.fixture(scope="session")
def config():
    """ Create a config object.

    Bootstrap for:
    - docker: we will want the docker client plugin registered
    - kubernetes: we will want the kubernetes client plugin registered
    - terraform: make its provisioner plugin availble for a launchapad
        backend
    - mtt: add some common config and detect mtt presets
    """

    # Use the mtt configerus.config.Config factory, but include the mtt
    # bootstrapping for it.  See the bootstrappers such as the one ih
    # mtt/__init__.py

    config = mtt.new_config(additional_bootstraps=[
        'docker',
        'kubernetes',
        'terraform',
        'mtt'
    ])

    # This does a lot of magic, potentially too much.  We use this because we
    # found that we had the same configerus building approach on a lot of test
    # suites, so we put it all in a common place.
    # Configerus provides bootstrap functionality for this purpose.

    return config


@pytest.fixture(scope='session')
def provisioner(config):
    """ Retrieve a provisioner object

    Use this if your test-cases want unprovisioned resources, but then they
    need to manage startup and teardown themselves.

    @see provisioner_up

    """
    return mtt.new_provisioner_from_config(config)


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

    conf = config.load(MTT_COMMON_CONFIG_LABEL)

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

    # Allow some config to tell us to keep the provisioner (for debugging)
    if not conf.get(MTT_COMMON_CONFIG_KEY_KEEPONFINISH,
                    exception_if_missing=False):
        try:
            logger.info(
                "Stopping the test cluster using the provisioner as directed by config")
            provisioner.destroy()
        except Exception as e:
            logger.error("Provisioner failed to stop: %s", e)
            raise e
    else:
        logger.info("Leaving test infrastructure in place on shutdown")
