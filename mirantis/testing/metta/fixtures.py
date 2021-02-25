"""

A set of plugin instances kept as a managed set, we call these fixtures

"""
import logging
from typing import Dict, List, Any

from .plugin import (METTAPlugin, Type, METTA_PLUGIN_CONFIG_KEY_PLUGINID,
                     METTA_PLUGIN_CONFIG_KEY_INSTANCEID, METTA_PLUGIN_CONFIG_KEY_TYPE,
                     METTA_PLUGIN_CONFIG_KEY_PRIORITY)

logger = logging.getLogger('metta.fixtures')

METTA_FIXTURES_CONFIG_FIXTURES_LABEL = 'fixtures'
""" A centralized configerus load label for multiple fixtures """
METTA_FIXTURES_CONFIG_FIXTURE_KEY = 'fixture'
""" Config .get() key for a single fixture """

METTA_FIXTURE_VALIDATION_JSONSCHEMA = {
    'type': 'object',
    'properties': {
        METTA_PLUGIN_CONFIG_KEY_PLUGINID: {'type': 'string'},
        METTA_PLUGIN_CONFIG_KEY_INSTANCEID: {'type': 'string'},
        METTA_PLUGIN_CONFIG_KEY_TYPE: {'type': 'string'},
        METTA_PLUGIN_CONFIG_KEY_PRIORITY: {
            'type': 'integer', 'minimum': 1, 'maximum': 100}
    },
    'required': [METTA_PLUGIN_CONFIG_KEY_PLUGINID]
}
""" json schema validation definition for a plugin """


class Fixture:
    """ A plugin wrapper struct that keep metadata about the plugin in a set """

    def __init__(self, plugin: object, type: Type,
                 plugin_id: str, instance_id: str, priority: int):
        """

        Parameters:
        -----------

        fixture : the fixture plugin instance

        Filtering parameters:

        type (.plugin.Type|str) : Type of plugin
        plugin_id (str) : registry plugin_id
        instance_id (str) : plugin instance identifier

        """
        self.type = type
        self.plugin_id = plugin_id
        self.instance_id = instance_id
        self.priority = priority
        self.plugin = plugin


class Fixtures:
    """ A set if plugins as a managed set

    A set of plugins that can be added in an arbitrary order but retrieved
    using filters and sorting.

    """

    def __init__(self):
        self.fixtures = []

    def __len__(self) -> int:
        """ Return how many plugin instances we have """
        return self.count()

    def __getitem__(self, instance_id: str) -> object:
        """ Handle subscription request

        For subscriptions assume that an instance_id is being retrieved and that
        a plugin is desired for return.

        Parameters:
        -----------

        instance_id (str) : Instance instance_id to look for

        Returns:

        Plugin object for highest priority plugin with the matching instance_id

        Raises:
        -------

        KeyError if the key cannot be matched,

        """
        return self.get_plugin(instance_id=instance_id)

    def merge_fixtures(self, merge_from: 'Fixtures'):
        """ merge fixture instances from another Fixtures object into this one

        Parameters:
        -----------

        merge_from (Fixtures) : fixture instance source

        """
        self.fixtures += merge_from.fixtures

    def new_fixture(self, plugin: object, type: Type,
                    plugin_id: str, instance_id: str, priority: int):
        """ Add a new fixture by providing the plugin instance and the metadata

        Create a new Fixture from the passed arguments and add it to the Fixtures set

        Parameters:
        -----------

        plugin : the fixture plugin instance

        Filtering parameters:

        type (.plugin.Type|str) : Type of plugin
        plugin_id (str) : registry plugin_id
        instance_id (str) : plugin instance identifier

        """
        fixture = Fixture(
            type=type,
            plugin_id=plugin_id,
            instance_id=instance_id,
            priority=priority,
            plugin=plugin)
        self.fixtures.append(fixture)
        return fixture

    def add_fixture(self, fixture: Fixture):
        """ Add an existing fixture

        Parameters:
        -----------

        fixture (Fixture) : existing fixture to add

        """
        self.fixtures.append(fixture)
        return fixture

    def to_list(self):
        """ retrieve this fixtures as a list """
        return sort_instance_list(self.fixtures)

    def count(self, type: Type = None, plugin_id: str = '',
              instance_id: str = ''):
        """ retrieve the first matching fixture object based on filters and priority

        Parameters:
        -----------

        Filtering parameters:

        type (.plugin.Type|str) : Type of plugin
        plugin_id (str) : registry plugin_id
        instance_id (str) : plugin instance identifier

        Returns:
        --------

        The fixture plugin object the sorted plugins that match the passed parameters,

        Raises:
        -------

        KeyError if exception_if_missing is True and no matching fixture was found

        """
        return len(self._filter_instances(
            type=type, plugin_id=plugin_id, instance_id=instance_id))

    def get_plugin(self, type: Type = None, plugin_id: str = '',
                   instance_id: str = '', exception_if_missing: bool = True):
        """ retrieve the first matching fixture object based on filters and priority

        Parameters:
        -----------

        Filtering parameters:

        type (.plugin.Type|str) : Type of plugin
        plugin_id (str) : registry plugin_id
        instance_id (str) : plugin instance identifier

        Returns:
        --------

        The highest priority matched Fixture fixture.
        If now fixtures matched, and exception_if_missing is False, then None

        Raises:
        -------

        KeyError if exception_if_missing is True and no matching fixture was found

        """
        instance = self.get_fixture(
            type=type,
            plugin_id=plugin_id,
            instance_id=instance_id,
            exception_if_missing=exception_if_missing)

        if not instance is None:
            return instance.plugin

    def get_fixture(self, type: Type = None, plugin_id: str = '',
                    instance_id: str = '', exception_if_missing: bool = True) -> 'Fixture':
        """ retrieve the first matching fixture object based on filters and priority

        Parameters:
        -----------

        Filtering parameters:

        type (.plugin.Type|str) : Type of plugin
        plugin_id (str) : registry plugin_id
        instance_id (str) : plugin instance identifier

        Returns:
        --------

        The highest priority matched Fixture fixture.
        If now fixtures matched, and exception_if_missing is False, then None

        Raises:
        -------

        KeyError if exception_if_missing is True and no matching fixture was found

        """
        instances = self.get_fixtures(
            type=type,
            plugin_id=plugin_id,
            instance_id=instance_id).to_list()

        if len(instances):
            return instances[0]
        if exception_if_missing:
            raise KeyError(
                "Could not find any matching fixture instances [type:{type}][plugin_id:{plugin_id}][instance_id:{instance_id}]".format(
                    type=type.value if not type is None else '',
                    plugin_id=plugin_id,
                    instance_id=instance_id))
        return None

    def get_plugins(self, type: Type = None, plugin_id: str = '',
                    instance_id: str = '') -> List[object]:
        """ retrieve the first matching fixture object based on filters and priority

        Parameters:
        -----------

        Filtering parameters:

        type (.plugin.Type|str) : Type of plugin
        plugin_id (str) : registry plugin_id
        instance_id (str) : plugin instance identifier

        Returns:
        --------

        A List of sorted Fixture fixture objects that match the arguments,
        possibly empty.

        """
        instances = self.get_fixtures(
            type=type,
            plugin_id=plugin_id,
            instance_id=instance_id).to_list()
        return [instance.plugin for instance in instances]

    def get_fixtures(self, type: Type = None, plugin_id: str = '',
                     instance_id: str = '') -> 'Fixtures':
        """ Retrieve an ordered filtered list of Fixtures

        Parameters:
        -----------

        Filtering parameters:

        type (.plugin.Type|str) : Type of plugin
        plugin_id (str) : registry plugin_id
        instance_id (str) : plugin instance identifier

        Returns:
        --------

        A List of Fixture structs that matched the arguments,
        possibly empty.
        If you want a sorted list see .to_list()

        """
        matches = Fixtures()
        [matches.add_fixture(match) for match in self._filter_instances(
            type=type, plugin_id=plugin_id, instance_id=instance_id)]
        return matches

    def get_filtered(self, type: Type = None,
                     plugin_id: str = '', instance_id: str = '') -> 'Fixtures':
        """ Get a new Fixtures object which is a filtered subset of this one """
        filtered = Fixtures()
        for instance in self._filter_instances(
                type=type, plugin_id=plugin_id, instance_id=instance_id):
            filtered.add_fixture(instance)
        return filtered

    def _filter_instances(self, type: Type = None,
                          plugin_id: str = '', instance_id: str = '') -> List[Fixture]:
        """ Filter the fixture instances down to a List

        Parameters:
        -----------

        Filtering parameters:

        type (.plugin.Type|str) : Type of plugin
        plugin_id (str) : registry plugin_id
        instance_id (str) : plugin instance identifier

        Returns:
        --------

        An unsorted List of Fixture structs that matched the arguments,
        possibly empty.

        Raises:
        -------

        KeyError if exception_if_missing is True and no matching fixture was found

        """
        matched_instances = []
        for plugin_instance in self.fixtures:
            # Could have one-lined this into a lambda but it would be
            # unreadable

            if plugin_id and not plugin_instance.plugin_id == plugin_id:
                continue
            elif instance_id and not plugin_instance.instance_id == instance_id:
                continue
            elif type and not type == plugin_instance.type:
                continue

            matched_instances.append(plugin_instance)

        return matched_instances


def sort_instance_list(list: List[Fixture]) -> List[Fixture]:
    """ Order a list of objects with a priority value from highest to lowest """
    return sorted(list, key=lambda i: 1 / i.priority if i.priority else 0)


class UCCTFixturesPlugin:
    """ Mixin class for output plugins that receives arguments """

    def __init__(self, fixtures: Fixtures = None):
        """ A Plugin that holds fixtures

        """
        if fixtures is None:
            fixtures = Fixtures()
        self.fixtures = fixtures
        """ Hold plugin fixtures, so that a provisioner can add output/clients etc """

    def get_fixtures(self, type: Type = None, instance_id: str = '',
                     plugin_id: str = '') -> Fixtures:
        """ retrieve an fixture plugin from the plugin """
        return self.fixtures.get_fixtures(
            type=type, plugin_id=plugin_id, instance_id=instance_id)

    def get_fixture(self, type: Type = None, instance_id: str = '',
                    plugin_id: str = '', exception_if_missing: bool = True) -> Fixture:
        """ retrieve an fixture plugin from the plugin """
        return self.fixtures.get_fixture(
            type=type, plugin_id=plugin_id, instance_id=instance_id, exception_if_missing=exception_if_missing)

    def get_plugin(self, type: Type = None, plugin_id: str = '',
                   instance_id: str = '', exception_if_missing: bool = True) -> METTAPlugin:
        """ Retrieve one of the passed in fixtures """
        logger.info(
            "{}:execute: get_plugin({})".format(
                self.instance_id,
                type.value))
        return self.fixtures.get_plugin(
            type=type, plugin_id=plugin_id, instance_id=instance_id, exception_if_missing=exception_if_missing)

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
