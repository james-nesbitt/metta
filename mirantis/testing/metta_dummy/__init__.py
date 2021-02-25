"""

metta Dummy

Dummy plugin functionality.  Various plugins that can be used as placeholders
and for testing.

"""

import logging
from typing import Any, Dict

from configerus.loaded import LOADED_KEY_ROOT

from mirantis.testing.metta.plugin import Factory, Type
from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.provisioner import METTA_PROVISIONER_CONFIG_PROVISIONER_LABEL

from .provisioner import DummyProvisionerPlugin
from .client import DummyClientPlugin
from .workload import DummyWorkloadPlugin

METTA_PLUGIN_ID_DUMMY = 'dummy'
""" All of the dummy plugins use 'dummy' as their plugin_id """


@Factory(type=Type.PROVISIONER, plugin_id=METTA_PLUGIN_ID_DUMMY)
def metta_plugin_factory_provisioner_dummy(
        environment: Environment, instance_id: str = '', fixtures: Dict[str, Dict[str, Any]] = {}):
    """ create an metta provisionersss dict plugin """
    return DummyProvisionerPlugin(environment, instance_id, fixtures)


@Factory(type=Type.CLIENT, plugin_id=METTA_PLUGIN_ID_DUMMY)
def metta_plugin_factory_client_dummy(
        environment: Environment, instance_id: str = '', fixtures: Dict[str, Dict[str, Any]] = {}):
    """ create an metta client dict plugin """
    return DummyClientPlugin(environment, instance_id, fixtures)


@Factory(type=Type.WORKLOAD, plugin_id=METTA_PLUGIN_ID_DUMMY)
def metta_plugin_factory_workload_dummy(
        environment: Environment, instance_id: str = '', fixtures: Dict[str, Dict[str, Any]] = {}):
    """ create an metta workload dict plugin """
    return DummyWorkloadPlugin(environment, instance_id, fixtures)


""" SetupTools EntryPoint METTA BootStrapping """


def bootstrap(environment: Environment):
    """ METTA_Dummy bootstrap

    We dont't take any action.  Our purpose is to run the above factory
    decorators to register our plugins.

    """
    pass
