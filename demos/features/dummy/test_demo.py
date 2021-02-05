import logging
import pytest
import pathlib
import getpass
from datetime import datetime
import os.path

logger = logging.getLogger(__file__)

DIR = str(pathlib.Path(__file__).parent.absolute())
""" Absolute path to this file, used as a root path """

# Import the mtt core
import mirantis.testing.mtt as mtt
# import mtt_dummy as we are going to use plugins from that package
import mirantis.testing.mtt_dummy as mtt_dummy

@pytest.fixture(scope='session')
def config():
    """ Create a config object. """

    config = mtt.new_config()

    return config

@pytest.fixture(scope="session")
def provisioner(config):
    """ get a provisioner based on the config """
    return mtt.provisioner_from_config(config)


def test_provisioner(provisioner):
    """ show how you would use the provisioner

    the provisioner.yml file configures our provisioner to be the "dummy" plugin
    which doesn't actually do anything, but this shows how you could do it.

    You probably want to `up()` the provisioner in the fixture instead of here
    so that the time spent bringing up/down the cluster isn't reflected in the
    test.

    """

    provisioner.prepare()
    provisioner.up()

    assert True, "This will never fail"

    provisioner.down()

def test_client(provisioner):
    """ test that we can get a proper client """
