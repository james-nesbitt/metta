
import logging
import pytest

logger = logging.getLogger(__file__)

import mirantis.testing.mtt as mtt
import mirantis.testing.mtt_common as mtt_common

@pytest.fixture()
def config():
    """ Create a common Config """

    conf = mtt.new_config()

    conf.add_source(mtt_common.MTT_PLUGIN_ID_CONFIGSOURCE_DICT).set_data({
        'mtt': {
            'one': 1,
            'two': {
                'one': 2.1,
                'two': 2.2,
            }
        }
    })

    return conf

def test_config_sane(config):
    """ some config sanity tests """

    mtt_conf = config.load('mtt')

    assert mtt_conf.get('one') == 1
    assert mtt_conf.get('two.one') == 2.1
    assert not mtt_conf.get('two.two') == 3
