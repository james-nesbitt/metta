
import logging
import pytest

logger = logging.getLogger(__file__)

import mirantis.testing.mtt as mtt
import mirantis.testing.mtt_common as mtt_common

# we will use dummy plugins here so we need to import them
import mirantis.testing.mtt_dummy as mtt_dummy

@pytest.fixture()
def config():
    """ Create a common Config """

    conf = mtt.new_config()

    conf.add_source(mtt_common.MTT_PLUGIN_ID_CONFIGSOURCE_DICT).set_data({
        'provisioner': {
            'plugin_id': mtt_dummy.MTT_PLUGIN_ID_DUMMY
        },
        'workloads': {
            'workloads': {
                'dummy': {
                    'plugin_id': mtt_dummy.MTT_PLUGIN_ID_DUMMY
                }
            }
        }
    })

    return conf

@pytest.fixture()
def provisioner(caplog, config):
    """ Create provisioner as defined by config """
    caplog.set_level(logging.DEBUG)
    return mtt.new_provisioner_from_config(config)

@pytest.fixture()
def workloads(caplog, config):
    """ Create a Dict of workload plugins """
    return mtt.new_workloads_from_config(config)

def test_config_is_sane(config):
    """ some config sanity tests """

    assert isinstance(config, mtt.config.Config)

def test_workload_loading(workloads):
    """ Do some workload testing """

    assert 'dummy' in workloads

def test_provisioner_run(caplog, provisioner):
    """ simulate a provisioned test run """

    assert isinstance(provisioner, mtt.provisioner.ProvisionerBase)

    provisioner.apply()

    assert True, "Run some test functionality here"

    provisioner.destroy()
