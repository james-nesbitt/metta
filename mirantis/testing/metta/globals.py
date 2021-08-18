"""

Global mutables.

Keep all package global variables in this module.

"""
from configerus.config import Config
from configerus.contrib.dict import PLUGIN_ID_SOURCE_DICT as CONFIGERUS_SOURCE_DICT

from mirantis.testing.metta.fixture import Fixtures

# A global config object, which metta will create if needed.  This is not
# Absolutely required, but it makes sense in scenarios where Metta is asked
# to bootstrap itself and discover environments.
global_config: Config = Config()
global_config.add_source(
    plugin_id=CONFIGERUS_SOURCE_DICT, instance_id="metta-global", priority=10
).set_data({"metta": {"instance_id": "metta"}})

# The global fixtures set allows us to manage session/global based fixtures
# which allows us to keep components such as environments as plugins, and
# to use them in a global scope.
global_fixtures: Fixtures = Fixtures()
""" Keep a set fixtures which are kept in global scope """
