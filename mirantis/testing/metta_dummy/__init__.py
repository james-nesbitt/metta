"""

METTA Dummy.

Dummy plugin functionality.  Various plugins that can be used as placeholders
and for testing.

"""

import logging
from typing import Any, Dict

from mirantis.testing.metta.plugin import Factory
from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.provisioner import METTA_PLUGIN_TYPE_PROVISIONER
from mirantis.testing.metta.client import METTA_PLUGIN_TYPE_CLIENT
from mirantis.testing.metta.workload import METTA_PLUGIN_TYPE_WORKLOAD

from .provisioner import DummyProvisionerPlugin
from .client import DummyClientPlugin
from .workload import DummyWorkloadPlugin

logger = logging.getLogger('metta.dummy')

METTA_PLUGIN_ID_DUMMY = 'dummy'
""" All of the dummy plugins use 'dummy' as their plugin_id """


@Factory(plugin_type=METTA_PLUGIN_TYPE_PROVISIONER, plugin_id=METTA_PLUGIN_ID_DUMMY)
def metta_plugin_factory_provisioner_dummy(environment: Environment, instance_id: str = '',
                                           fixtures: Dict[str, Dict[str, Any]] = None):
    """Create an metta provisionersss dict plugin."""
    return DummyProvisionerPlugin(environment, instance_id, fixtures)


@Factory(plugin_type=METTA_PLUGIN_TYPE_CLIENT, plugin_id=METTA_PLUGIN_ID_DUMMY)
def metta_plugin_factory_client_dummy(environment: Environment, instance_id: str = '',
                                      fixtures: Dict[str, Dict[str, Any]] = None):
    """Create an metta client dict plugin."""
    return DummyClientPlugin(environment, instance_id, fixtures)


@Factory(plugin_type=METTA_PLUGIN_TYPE_WORKLOAD, plugin_id=METTA_PLUGIN_ID_DUMMY)
def metta_plugin_factory_workload_dummy(environment: Environment, instance_id: str = '',
                                        fixtures: Dict[str, Dict[str, Any]] = None):
    """Create an metta workload dict plugin."""
    return DummyWorkloadPlugin(environment, instance_id, fixtures)


# ----- SetupTools EntryPoint METTA BootStrapping -----


# pylint: disable=unused-argument
def bootstrap(environment: Environment):
    """METTA_Terraform bootstrap.

    Currently we only use this to import plugins.

    Parameters:
    -----------
    env (Environment) : an environment which should have validation config added to.

    """
