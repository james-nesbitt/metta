"""

MTT Dummy

Dummy plugin functionality.  Various plugins that can be used as placeholders
and for testing.

"""

from configerus.config import Config

from mirantis.testing.mtt import plugin as mtt_plugin

from .plugins.provisioner import DummyProvisionerPlugin
from .plugins.client import DummyClientPlugin
from .plugins.workload import DummyWorkloadPlugin

MTT_PLUGIN_ID_DUMMY = 'dummy'
""" All of the dummy plugins use 'dummy' as their plugin_id """

""" provisioner plugin_id for the mtt dummy plugin """
@mtt_plugin.Factory(type=mtt_plugin.Type.PROVISIONER, plugin_id=MTT_PLUGIN_ID_DUMMY)
def mtt_plugin_factory_provisioner_dummy(config:Config, instance_id: str = ''):
    """ create an mtt provisionersss dict plugin """
    return DummyProvisionerPlugin(config, instance_id)

""" client plugin_id for the mtt dummy plugin """
@mtt_plugin.Factory(type=mtt_plugin.Type.CLIENT, plugin_id=MTT_PLUGIN_ID_DUMMY)
def mtt_plugin_factory_client_dummy(config:Config, instance_id: str = ''):
    """ create an mtt client dict plugin """
    return DummyClientPlugin(config, instance_id)

""" workload plugin_id for the mtt dummy plugin """
@mtt_plugin.Factory(type=mtt_plugin.Type.WORKLOAD, plugin_id=MTT_PLUGIN_ID_DUMMY)
def mtt_plugin_factory_workload_dummy(config:Config, instance_id: str = ''):
    """ create an mtt workload dict plugin """
    return DummyWorkloadPlugin(config, instance_id)


def configerus_bootstrap(config:Config):
    """ MTT_Dummy configerus bootstrap

    We dont't take any action.  Our purpose is to run the above factory
    decorators to register our plugins.

    """
    pass
