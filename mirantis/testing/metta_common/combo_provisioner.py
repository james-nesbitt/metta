"""

A provisioner that combines multiple provisioners

"""
import logging
from typing import Dict, List, Any

from configerus.loaded import LOADED_KEY_ROOT
from mirantis.testing.metta.plugin import METTAPlugin, Type
from mirantis.testing.metta.fixtures import Fixtures, Fixture, UCCTFixturesPlugin
from mirantis.testing.metta.provisioner import ProvisionerBase

logger = logging.getLogger('metta.contrib.provisioner:combo')

COMBO_PROVISIONER_CONFIG_LABEL = 'provisioner'
""" Configerus label for loading config to set up this provisioner plugin """
COMBO_PROVISIONER_CONFIG_BACKENDS_KEY = 'backends'
""" Config key for backends list """


class ComboProvisionerPlugin(ProvisionerBase, UCCTFixturesPlugin):
    "Combo Provisioner plugin class"

    def __init__(self, environment, instance_id,
                 label: str = COMBO_PROVISIONER_CONFIG_LABEL, base: Any = LOADED_KEY_ROOT):
        """ Run the super constructor but also set class properties

        Interpret provided config and configure the object with all of the needed
        pieces for executing terraform commands

        """
        ProvisionerBase.__init__(self, environment, instance_id)
        UCCTFixturesPlugin.__init__(self)

        logger.info("Preparing Combo provisioner")

        try:
            self.combo_config = self.environment.config.load(label)
        except KeyError as e:
            raise ValueError(
                "Combo provisioner could not find any configurations: {}".format(e)) from e

        self.backends = self.combo_config.get(
            [base, COMBO_PROVISIONER_CONFIG_BACKENDS_KEY])
        if not isinstance(self.backends, list):
            raise ValueError(
                "Combo provisioner could not understand the backend list.")

        for backend in self.backends:
            backend_instance_id = backend['instance_id']
            fixture = self.environment.fixtures.get_fixture(
                type=Type.PROVISIONER, instance_id=backend_instance_id)

            if hasattr(backend, "priority"):
                fixture.priority = backend['priority']

            self.fixtures.add_fixture(fixture)

    def _get_ordered_backend_fixtures(self, high_to_low: bool = False):
        """ helper to get the sorted backend fixtures from lowest priority to highest, reversed if requested """
        backend_fixtures = self.fixtures.get_fixtures(
            type=Type.PROVISIONER).to_list()
        if not high_to_low:
            backend_fixtures.reverse
        return backend_fixtures

    def info(self):
        """ return structured data about self. """

        backends_info = []
        for fixture in self._get_ordered_backend_fixtures():
            backend_info = {
                'fixture': {
                    'type': fixture.type.value,
                    'instance_id': fixture.instance_id,
                    'plugin_id': fixture.plugin_id
                }
            }

            plugin = fixture.plugin
            if hasattr(plugin, 'info'):
                backend_info.update(plugin.info())

            if not 'fixture' in backend_info:
                backend_info

            backends_info.append(backend_info)

        return {
            'backends': backends_info
        }

    def prepare(self, label: str = '', base: str = ''):
        """ Prepare the provisioner to apply resources """
        for backend_fixture in self._get_ordered_backend_fixtures():
            logger.info(
                "--> running backend prepare: [Low->High] {}".format(backend_fixture.instance_id))
            backend_fixture.plugin.prepare()

    def apply(self):
        """ bring a cluster to the configured state """
        for backend_fixture in self._get_ordered_backend_fixtures():
            logger.info(
                "--> running backend apply: [Low->High] {}".format(backend_fixture.instance_id))
            backend_fixture.plugin.apply()

    def destroy(self):
        """ remove all resources created for the cluster """
        for backend_fixture in self._get_ordered_backend_fixtures(
                high_to_low=True):
            logger.info(
                "--> running backend destroy: [High->Low] {}".format(backend_fixture.instance_id))
            backend_fixture.plugin.destroy()

    """ Fixture management """

    def get_fixtures(self, type: Type = None, instance_id: str = '',
                     plugin_id: str = '') -> Fixtures:
        """ retrieve any matching fixtures from any of the backends """
        matches = Fixtures()
        for backend_fixture in self._get_ordered_backend_fixtures():
            plugin = backend_fixture.plugin
            if hasattr(plugin, 'get_fixtures'):
                for match in plugin.get_fixtures(
                        type=type, plugin_id=plugin_id, instance_id=instance_id).to_list():
                    matches.add_fixture(match)
        return matches

    def get_fixture(self, type: Type = None, instance_id: str = '',
                    plugin_id: str = '', exception_if_missing: bool = True) -> Fixture:
        """ retrieve the first matching fixture fomr backend in high-to-low order """

        for backend_fixture in self._get_ordered_backend_fixtures(
                high_to_low=True):
            plugin = backend_fixture.plugin
            if hasattr(plugin, 'get_fixture'):
                fixture = plugin.get_fixture(
                    type=type,
                    plugin_id=plugin_id,
                    instance_id=instance_id,
                    exception_if_missing=exception_if_missing)
                if fixture is not None:
                    return fixture

        if exception_if_missing:
            raise KeyError("No matching fixture was found")

    def get_plugin(self, type: Type = None, plugin_id: str = '',
                   instance_id: str = '', exception_if_missing: bool = True) -> METTAPlugin:
        """ Retrieve one of the passed in fixtures """
        logger.info(
            "{}:execute: get_plugin({})".format(
                self.instance_id,
                type.value))
        fixture = self.get_fixture(
            type=type, plugin_id=plugin_id, instance_id=instance_id, exception_if_missing=exception_if_missing)

        if fixture is not None:
            return fixture.plugin

    def get_provisioner(self, plugin_id: str = '', instance_id: str = '',
                        exception_if_missing: bool = True) -> METTAPlugin:
        """ Retrieve one of the passed in fixture provisioner """
        return self.get_plugin(type=Type.PROVISIONER, plugin_id=plugin_id,
                               instance_id=instance_id, exception_if_missing=exception_if_missing)

    def get_output(self, plugin_id: str = '', instance_id: str = '',
                   exception_if_missing: bool = True) -> METTAPlugin:
        """ Retrieve one of the passed in fixture outputs """
        return self.get_plugin(type=Type.OUTPUT, plugin_id=plugin_id,
                               instance_id=instance_id, exception_if_missing=exception_if_missing)

    def get_client(self, plugin_id: str = '', instance_id: str = '',
                   exception_if_missing: bool = True) -> METTAPlugin:
        """ Retrieve one of the passed in fixture clients """
        return self.get_plugin(type=Type.CLIENT, plugin_id=plugin_id,
                               instance_id=instance_id, exception_if_missing=exception_if_missing)

    def get_workload(self, plugin_id: str = '', instance_id: str = '',
                     exception_if_missing: bool = True) -> METTAPlugin:
        """ Retrieve one of the passed in fixture workloads """
        return self.get_plugin(type=Type.WORKLOAD, plugin_id=plugin_id,
                               instance_id=instance_id, exception_if_missing=exception_if_missing)
