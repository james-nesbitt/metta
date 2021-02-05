import logging
import pytest

logger = logging.getLogger('mtt ltc demo')

# Import the mtt core
import mirantis.testing.mtt as mtt

""" Define our fixtures """

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
        'mtt_mirantis_common',
        'mtt_terraform'
    ])

    # This does a lot of magic, potentially too much.  We use this because we
    # found that we had the same configerus building approach on a lot of test
    # suites, so we put it all in a common place.
    # Configerus provides bootstrap functionality for this purpose.

    return config

@pytest.fixture(scope='session')
def provisioner():
    """ pretend to build a provisioner which will be overloaded by matrix """
    return None
