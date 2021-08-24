"""

Dummy metta provisioner plugin

A provisioner which doesn't do anything, but can still be configured to produce
various clients and outputs.  The provisioner has no significant requirements
and no impact.  Provisioning can be repeated or interupted without impact.

The dummy provisioner is entirely config based.  Use the prepare() method to
indicate an appropriate config source and the provisioner will do the rest. As
long as you match its config convention it can take care of itself.

"""

import logging
from typing import Dict, Any

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.fixture import Fixtures

logger = logging.getLogger("metta.contrib.dummy.provisioner")


class DummyProvisionerPlugin:
    """Dummy provisioner class"""

    def __init__(
        self,
        environment: Environment,
        instance_id: str,
        fixtures: Dict[str, Dict[str, Any]] = None,
    ):
        self._environment: Environment = environment
        """ Environemnt in which this plugin exists """
        self._instance_id: str = instance_id
        """ Unique id for this plugin instance """

        self.fixtures = Fixtures()
        """This plugin keeps fixtures."""
        if fixtures is not None:
            for child_instance_id, child_instance_dict in fixtures.items():
                child = environment.add_fixture_from_dict(
                    instance_id=child_instance_id, plugin_dict=child_instance_dict
                )
                self.fixtures.add(child)

    def apply(self):
        """pretend to bring a cluster up"""
        logger.info("%s:execute: apply()", self._instance_id)

    def prepare(self):
        """pretend to prepare the cluster"""
        logger.info("%s:execute: apply()", self._instance_id)

    def destroy(self):
        """pretend to brind a cluster down"""
        logger.info("%s:execute: apply()", self._instance_id)
