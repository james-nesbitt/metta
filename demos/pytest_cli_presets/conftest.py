from mirantis.testing.mtt.presets import MTT_MIRANTIS_PRESETS, MTT_MIRANTIS_PRESET_CONFIG_LABEL, add_preset_config
import mirantis.testing.mtt as mtt
import logging
import pytest
import pathlib
import getpass
from datetime import datetime
import os.path

logging.basicConfig(encoding='utf-8', level=logging.INFO)
logger = logging.getLogger('mtt ltc demo')

DIR = str(pathlib.Path(__file__).parent.absolute())
""" Absolute path to this file, used as a root path """

# Import the mtt core

# Defaults / keys related to cli options

PRESET_FLAG_TEMPLATE = '--{}'
""" string format template for a preset key """
PRESET_DEFAULTS = {
    'variation': 'ltc'
}
""" Set some default values for the presets, so that they don't all need to
    be passed """


def pytest_addoption(parser):
    """ Add pytest cli options to allow all mtt_presets """

    # Add a --{preset_key} option for each available preset, including a default
    # if wecan find one in PRESET_DEFAULTS
    for preset in MTT_MIRANTIS_PRESETS:
        preset_key = preset[0]
        preset_default = PRESET_DEFAULTS[preset_key] if preset_key in PRESET_DEFAULTS else ''
        parser.addoption(
            PRESET_FLAG_TEMPLATE.format(preset_key),
            action="store",
            default=preset_default)


@pytest.fixture(scope='session')
def config(request):
    """ Create a config object.

    Bootstrap for:
    - mtt: add some common config
    - mtt_terraform: we will want the terraform provisioner plugin

    We then interpret pytest options and build a preset list and re-run the
    mtt operation for detecting presets

    """

    # Use the mtt configerus.config.Config factory, but include the mtt
    # bootstrapping for it.  See the bootstrappers such as the one in
    # mtt/__init__.py

    config = mtt.new_config(additional_bootstraps=[
        'mtt_common',
        'mtt_terraform'
    ])

    # discover an mtt presets that we set as pytest cli flags
    mtt_preset_config = {}
    for preset in MTT_MIRANTIS_PRESETS:
        preset_key = preset[0]
        preset_value = request.session.config.getoption(
            PRESET_FLAG_TEMPLATE.format(preset_key))
        if preset_value:
            mtt_preset_config[preset_key] = preset_value
    # Add a config source that sets the prests in the manner that mtt expects
    # { mtt: { [preset_key]: [preset_value]... }}
    config.add_source(mtt.SOURCE_DICT, 'cli_presets', priority=config.default_priority() + 1).set_data(
        MTT_MIRANTIS_PRESET_CONFIG_LABEL: mtt_preset_config
    )

    # tell mtt to look for presets again, to discover our new presets
    config.bootstrap('mtt_presets')

    return config


@pytest.fixture(scope="session")
def provisioner(config):
    """ get a provisioner based on the config """
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

    if conf.get("destroy-on-finish", exception_if_missing=False):
        try:
            logger.info(
                "Stopping the test cluster using the provisioner as directed by config")
            provisioner.destroy()
        except Exception as e:
            logger.error("Provisioner failed to stop: %s", e)
            raise e
    else:
        logger.info("Leaving test infrastructure in place on shutdown")
