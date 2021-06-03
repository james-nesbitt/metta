"""

A provisioner that combines multiple provisioners.

The combo provisioner keeps an ordered collection of "backend" provisioner
plugins which it proxies for any provisioner operations.

"""
import logging
from typing import Any

from configerus.loaded import LOADED_KEY_ROOT
from configerus.contrib.jsonschema.validate import PLUGIN_ID_VALIDATE_JSONSCHEMA_SCHEMA_CONFIG_LABEL
from configerus.validator import ValidationError

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.fixtures import Fixtures, Fixture
from mirantis.testing.metta.plugin import (METTA_PLUGIN_CONFIG_KEY_INSTANCEID,
                                           METTA_PLUGIN_CONFIG_KEY_PRIORITY)
from mirantis.testing.metta.provisioner import ProvisionerBase, METTA_PLUGIN_TYPE_PROVISIONER

logger = logging.getLogger('metta.contrib.provisioner:combo')

METTA_PLUGIN_ID_PROVISIONER_COMBO = 'combo'
""" provisioner plugin_id for the combo plugin """

COMBO_PROVISIONER_CONFIG_LABEL = 'provisioner'
""" Configerus label for loading config to set up this provisioner plugin """
COMBO_PROVISIONER_CONFIG_BACKENDS_KEY = 'backends'
""" Config key for backends list """

COMBO_PROVISIONER_VALIDATE_JSONSCHEMA = {
    'type': 'object',
    'properties': {
        'backends': {
            'type': 'array',
            "items": {"$ref": "#/$defs/backend"}
        }
    },
    "$defs": {
        "backend": {
            "type": "object",
            "required": ["instance_id"],
            "properties": {
                "instance_id": {
                    "type": "string",
                    "description": "Backend provisioner instance_id. A provisioner instance with "
                                   "this id  must exist in the environment."
                },
                "priority": {
                    "type": "boolean",
                    "description": "Backend provisioner priority in the combo list.  If not "
                                   "provided then The provisioner's priority will be used."
                }
            }
        }
    },
    'required': ['backends']
}
""" Validation jsonschema for terraform config contents """
COMBO_PROVISIONER_VALIDATE_TARGET = {
    PLUGIN_ID_VALIDATE_JSONSCHEMA_SCHEMA_CONFIG_LABEL: COMBO_PROVISIONER_VALIDATE_JSONSCHEMA
}


class ComboProvisionerPlugin(ProvisionerBase):
    """Combo Provisioner plugin class.

    This provisioner plugin is configered with a list of backends, which it
    will iterate across for every provisioner method call.  The backends have a
    priority which define the order of their call and every provisioner method
    will follow that order (or reverse it.)

    Parameters:
    -----------
    environment (Environment) : All metta plugins receive the environment
        object in which they were created.
    instance_id (str) : all metta plugins receive their own string identity.

    label (str) : Configerus load label for finding plugin config.
    base (str) : Configerus get base key in which the plugin should look for
        all config.

    """

    def __init__(self, environment: Environment, instance_id: str,
                 label: str = COMBO_PROVISIONER_CONFIG_LABEL, base: Any = LOADED_KEY_ROOT):
        """Run the super constructor but also set class properties.

        Interpret provided config and configure the object with all of the
        needed pieces for executing terraform commands

        """
        self.environment = environment
        """ Environemnt in which this plugin exists """
        self.instance_id = instance_id
        """ Unique id for this plugin instance """

        try:
            combo_config = self.environment.config.load(label)
        except KeyError as err:
            raise ValueError("Combo provisioner could not find any configurations") from err

        # Run confgerus validation on the config using our above defined jsonschema
        try:
            combo_config.get(base, validator=COMBO_PROVISIONER_VALIDATE_TARGET)
        except ValidationError as err:
            raise ValueError("Combo provisioner config failed validation") from err

        try:
            backends_list = combo_config.get([base, COMBO_PROVISIONER_CONFIG_BACKENDS_KEY])
            if not isinstance(backends_list, list):
                raise ValueError("Combo provisioner could not understand the backend list."
                                 " A list was expected.")
        except KeyError as err:
            raise ValueError("Combo provisioner received no backend list from config.") from err

        # for each of our string instance_ids we add the backend in order by finding if from the
        # environment and adding it to our UCCTFixturesPlugin fixtures list.
        self.backends = Fixtures()
        for backend in backends_list:
            backend_instance_id = backend[METTA_PLUGIN_CONFIG_KEY_INSTANCEID]
            try:
                fixture = self.environment.fixtures.get(
                    plugin_type=METTA_PLUGIN_TYPE_PROVISIONER, instance_id=backend_instance_id)
            except KeyError as err:
                raise ValueError(
                    "Combo provisioner was given a backend provisioner key that it could not "
                    f"correlate with a existing fixture: {backend_instance_id}") from err

            if hasattr(backend, METTA_PLUGIN_CONFIG_KEY_PRIORITY):
                fixture.priority = backend[METTA_PLUGIN_CONFIG_KEY_PRIORITY]

            self.backends.add(fixture)

    def _get_backend_iter(self, low_to_high: bool = False):
        """Get the sorted backend fixtures.

        Parameters:
        -----------
        low-to-high (bool) : ask for the fixtures in a lowest to highest
            (reverse) order.

        Returns:
        --------
        Iterator which is either the backends fixtures object, or the backends
            reversed()

        """
        if low_to_high:
            return reversed(self.backends)
        return self.backends

    def info(self):
        """Return structured data about self."""
        backends_info = []
        # List backends in high->low priority as this shows the order of apply
        for fixture in self.backends:
            backend_info = {
                'fixture': {
                    'type': fixture.plugin_type,
                    'instance_id': fixture.instance_id,
                    'plugin_id': fixture.plugin_id
                }
            }

            plugin = fixture.plugin
            if hasattr(plugin, 'info'):
                backend_info.update(plugin.info())

            backends_info.append(backend_info)

        return {
            'backends': backends_info
        }

    def prepare(self):
        """Prepare the provisioner to apply resources."""
        for backend_fixture in self._get_backend_iter():
            logger.info("--> running backend prepare: [High->Low] %s", backend_fixture.instance_id)
            backend_fixture.plugin.prepare()

    def apply(self):
        """Bring a cluster to the configured state."""
        for backend_fixture in self._get_backend_iter():
            logger.info("--> running backend apply: [High->Low] %s", backend_fixture.instance_id)
            backend_fixture.plugin.apply()

    def destroy(self):
        """Remove all resources created for the cluster."""
        for backend_fixture in self._get_backend_iter(low_to_high=True):
            logger.info("--> running backend destroy: [Low->High] %s", backend_fixture.instance_id)
            backend_fixture.plugin.destroy()

    # --- Fixture management
    #
    # We duplicate the UCCTFixturesPlugin methods, despite using it as a parent,
    # so that we can identify as that object, but because we need to allow all
    # backends to participate in fixture definition in order of priority.
    #
    # We of course have to override the any method which depends on our ordered
    # backend retrievals of get_fixtures() so that it doesn't run the parent
    # get_fixtures.

    def get_fixtures(self, plugin_type: str = '', instance_id: str = '',
                     plugin_id: str = '') -> Fixtures:
        """Retrieve any matching fixtures from any of the backends."""
        matches = Fixtures()
        for backend_fixture in self._get_backend_iter():
            plugin = backend_fixture.plugin
            if hasattr(plugin, 'fixtures'):
                matches.merge(plugin.fixtures.filter(plugin_type=plugin_type, plugin_id=plugin_id,
                                                     instance_id=instance_id))
        return matches

    def get_fixture(self, plugin_type: str = '', instance_id: str = '',
                    plugin_id: str = '', exception_if_missing: bool = True) -> Fixture:
        """Retrieve the first matching fixture from ordered backends."""
        matches = self.get_fixtures(plugin_type=plugin_type, plugin_id=plugin_id,
                                    instance_id=instance_id)

        if len(matches) > 0:
            return matches.get()

        if exception_if_missing:
            raise KeyError("No matching fixture was found")
        return None

    def get_plugin(self, plugin_type: str = '', plugin_id: str = '', instance_id: str = '',
                   exception_if_missing: bool = True) -> object:
        """Retrieve one of the passed in fixtures."""
        logger.info("%s:execute: get_plugin(%s)", self.instance_id, plugin_type)
        fixture = self.get_fixture(plugin_type=plugin_type, plugin_id=plugin_id,
                                   instance_id=instance_id,
                                   exception_if_missing=exception_if_missing)

        if fixture is not None:
            return fixture.plugin

        # this if is not needed, as get_fixture() handles exception_if_missing
        if exception_if_missing:
            raise KeyError("No matching plugin was found")
        return None
