import logging
import pytest
import pathlib
import getpass
from datetime import datetime
import os.path

logger = logging.getLogger('mtt ltc demo')

# Import the mtt core
import mirantis.testing.mtt as mtt

""" Define our fixtures """

@pytest.fixture(scope='session')
def dir():
    """ quick access to project root path """
    return DIR

@pytest.fixture(scope='session')
def config():
    """ Create a config object.

    Bootstrap for:
    - mtt_docker: we will want the docker client plugin registered
    - mtt_kubernetes: we will want the kubernetes client plugin registered
    - mtt_mirantis: add some common config and detect mtt_mirantis presets
    - mtt_terraform: make its provisioner plugin availble for a launchapad
        backend
    """

    # Use the mtt configerus.config.Config factory, but include the mtt
    # bootstrapping for it.  See the bootstrappers such as the one ih
    # mtt_mirantis/__init__.py

    config = mtt.new_config(additional_bootstraps=[
        'mtt_docker',
        'mtt_kubernetes',
        'mtt_mirantis',
        'mtt_terraform'
    ])

    # This does a lot of magic, potentially too much.  We use this because we
    # found that we had the same configerus building approach on a lot of test
    # suites, so we put it all in a common place.
    # Configerus provides bootstrap functionality for this purpose.

    return config

@pytest.fixture(scope='session')
def provisioner(config):
    """ Retrieve a provisioner object

    we only use one provisioned cluster in this test suite
    (but we still give it an arbitraty name)

    Use this if your test-cases want unprovisioned resources, but then they
    need to manage startup and teardown themselves.

    @see provisioner_up

    """
    return mtt.new_provisioner_from_config(config, 'ltc_provisioner')

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

    if not conf.get("keep-on-finish", exception_if_missing=False):
        try:
            logger.info("Stopping the test cluster using the provisioner as directed by config")
            provisioner.destroy()
        except Exception as e:
            logger.error("Provisioner failed to stop: %s", e)
            raise e
    else:
        logger.info("Leaving test infrastructure in place on shutdown")
