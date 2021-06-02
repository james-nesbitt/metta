"""

Fixture management code.

A Fixture is a plugin isntance wrapper that keeps metadata about the plugin
instance. A Fixtures object is a collection of plugin instances kept as an
ordered, managed set.

"""
import logging
from typing import List, Iterator

# pylint: disable=W0511
# TODO move these to this file as METTA_FIXTURE_KEY_XXXXX
from .plugin import (METTA_PLUGIN_CONFIG_KEY_PLUGINTYPE, METTA_PLUGIN_CONFIG_KEY_PLUGINID,
                     METTA_PLUGIN_CONFIG_KEY_INSTANCEID, METTA_PLUGIN_CONFIG_KEY_PRIORITY)

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
        METTA_PLUGIN_CONFIG_KEY_PLUGINTYPE: {'type': 'string'},
        METTA_PLUGIN_CONFIG_KEY_PRIORITY: {
            'type': 'integer', 'minimum': 1, 'maximum': 100}
    },
    'required': [METTA_PLUGIN_CONFIG_KEY_PLUGINID]
}
""" json schema validation definition for a plugin """


# pylint: disable=too-few-public-methods
class Fixture:
    """A plugin wrapper struct that keep metadata about the plugin in a set.

    pylint: R0903 ; if we replace this with a Dict then we have to define the
        key values as a constant set.  it would be cumbersome to import such
        things all over the place.

    """

    # pylint: disable=too-many-arguments
    def __init__(self, plugin: object, plugin_type: str, plugin_id: str, instance_id: str,
                 priority: int):
        """Initialize struct contents.

        Parameters:
        -----------
        plugin : the fixture plugin instance

        Filtering parameters:

        plugin_type (str) : Type of plugin
        plugin_id (str) : registry plugin_id
        instance_id (str) : plugin instance identifier

        """
        self.plugin_type = plugin_type
        self.plugin_id = plugin_id
        self.instance_id = instance_id
        self.priority = priority
        self.plugin = plugin

    def __eq__(self, other):
        """Compare to another fixture.

        Parameters:
        -----------
        other (Fixture) : fixture to compare this fixture against.

        Returns:
        --------
        Boolean True if the other fixture matches this one in metadata,
        otherwise False.

        """
        if not isinstance(other, Fixture):
            return False

        return (self.plugin_type == other.plugin_type
                and self.plugin_id == other.plugin_id
                and self.instance_id == other.instance_id)


class Fixtures:
    """A managed set of Fixture objects.

    A set of plugins that can be added in an arbitrary order but retrieved
    using filters and sorting.  The plugins are wrapped as Fixtures, which are
    used for the sorting and filtering.

    To use this, create an instance, and then add fixtures using either new()
    or add().  You can also combine two collections using merge().
    To get fixtures out, either iterator across the Fixtures object, or use
    get() to retrieve a single matching item.  use filter() to produce a new
    Fixtures object as a reduced set.

    """

    def __init__(self):
        """Create initial empty fixtures list."""
        self._fixtures: List[Fixture] = []
        """ object List of fixtures. """

    def __len__(self) -> int:
        """Return how many plugin instances we have.

        Returns:
        --------
        Integer length of the collection of Fixture objects.

        """
        return len(self._fixtures)

    def __iter__(self) -> Iterator[Fixture]:
        """Create an iterator for the fixtures object.

        @TODO switch to just using a generator?

        Returns:
        --------
        An Iterator of Fixture objects

        """
        # Iterate across the to_list() set, as it is sorted.
        return iter(self.to_list())

    def __reversed__(self) -> Iterator[Fixture]:
        """Create a reversed iterator for the fixtures object.

        @TODO switch to just using a generator?

        Returns:
        --------
        An Iterator of Fixture objects

        """
        # Iterate across the to_list() set, as it is sorted.
        return reversed(self.to_list())

    def merge(self, merge_from: 'Fixtures'):
        """Merge fixture instances from another Fixtures object into this one.

        Parameters:
        -----------
        Merge_from (Fixtures) : fixture instance source

        Raises:
        -------
        May raise a KeyError if there a matching plugin is already in the
        Fixtures object.

        (plugin_type/plugin_id/instance_id)

        """
        # We use the add_fixture method to centralize the logic for adding fixtures to one function
        for fixture in merge_from:
            self.add(fixture)

    # pylint: disable=too-many-arguments
    def new(self, plugin: object, plugin_type: str, plugin_id: str,
            instance_id: str, priority: int) -> Fixture:
        """Add a new fixture by providing the plugin instance and the metadata.

        Create a new Fixture from the passed arguments and add it to the
        Fixtures set.

        Parameters:
        -----------
        plugin : the fixture plugin instance

        Filtering parameters:

        plugin_type (str) : Type of plugin
        plugin_id (str) : registry plugin_id
        instance_id (str) : plugin instance identifier
        priority (int) : plugin priority

        """
        return self.add(Fixture(plugin_type=plugin_type, plugin_id=plugin_id,
                                instance_id=instance_id, priority=priority, plugin=plugin))

    def add(self, fixture: Fixture, allow_overwrite: bool = True) -> Fixture:
        """Add an existing fixture.

        If a matching

        Parameters:
        -----------
        fixture (Fixture) : existing fixture to add

        allow_overwrite (bool) : If True, then this fixture can replace a
            matching plugin with the same metadata.

        """
        if self.get(plugin_type=fixture.plugin_type, plugin_id=fixture.plugin_id,
                    instance_id=fixture.instance_id, exception_if_missing=False):

            if not allow_overwrite:
                raise KeyError("Fixture index already exists:"
                               f"[plugin_type:{fixture.plugin_type}][plugin_id:{fixture.plugin_id}]"
                               f"[instance_id:{fixture.instance_id}]")

            for i in range(len(self._fixtures)):
                if self._fixtures[i] == fixture:
                    self._fixtures[i] = fixture
                    return fixture

        self._fixtures.append(fixture)

        return fixture

    def get(self, plugin_type: str = '', plugin_id: str = '', instance_id: str = '',
            exception_if_missing: bool = True) -> Fixture:
        """Retrieve the first matching fixture object based on filters and priority.

        Parameters:
        -----------
        Filtering parameters:

        plugin_type (str) : Type of plugin
        plugin_id (str) : registry plugin_id
        instance_id (str) : plugin instance identifier

        Returns:
        --------
        The highest priority matched Fixture fixture.
        If now fixtures matched, and exception_if_missing is False, then None

        Raises:
        -------
        KeyError if exception_if_missing is True and no matching fixture was
        found.

        """
        filtered = self.filter(
            plugin_type=plugin_type,
            plugin_id=plugin_id,
            instance_id=instance_id)

        if len(filtered) > 0:
            return filtered.to_list()[0]
        if exception_if_missing:
            raise KeyError("Could not find any matching fixture instances "
                           f"[plugin_type:{plugin_type}][plugin_id:{plugin_id}]"
                           f"[instance_id:{instance_id}]")
        # filtered list was empty, and we were not directed to raise an exception for that.
        return None

    def get_plugin(self, plugin_type: str = '', plugin_id: str = '', instance_id: str = '',
                   exception_if_missing: bool = True) -> object:
        """Retrieve the first matching plugin  based on filters and priority.

        Parameters:
        -----------
        Filtering parameters:

        plugin_type (str) : Type of plugin
        plugin_id (str) : registry plugin_id
        instance_id (str) : plugin instance identifier

        Returns:
        --------
        The highest priority matched Fixture fixture.
        If now fixtures matched, and exception_if_missing is False, then None

        Raises:
        -------
        KeyError if exception_if_missing is True and no matching fixture was
        found. This error is actually raise in self.get()

        """
        fixture = self.get(
            plugin_type=plugin_type,
            plugin_id=plugin_id,
            instance_id=instance_id,
            exception_if_missing=exception_if_missing)

        if fixture is None:
            return None
        return fixture.plugin

    def filter(self, plugin_type: str = '', plugin_id: str = '', instance_id: str = '',
               exception_if_missing: bool = False) -> 'Fixtures':
        """Filter the fixture instances.

        Parameters:
        -----------
        Filtering parameters:

        plugin_type (str) : Type of plugin
        plugin_id (str) : registry plugin_id
        instance_id (str) : plugin instance identifier

        Returns:
        --------
        A new Fixtures object with only matching Fixture objects.  It could
        contain all of the items. If no filters were passed in, or it could
        be empty if no matches were found and the passed exception_is_missing
        variable is True

        Raises:
        -------
        KeyError if exception_if_missing is True and no matching fixture was found

        """
        filtered = Fixtures()
        for fixture in self._fixtures:
            # Could have one-lined this into a lambda but it would be
            # unreadable

            if plugin_type and not fixture.plugin_type == plugin_type:
                continue
            if plugin_id and not fixture.plugin_id == plugin_id:
                continue
            if instance_id and not fixture.instance_id == instance_id:
                continue

            filtered.add(fixture)

        if exception_if_missing and len(filtered) == 0:
            raise KeyError(f"Filter found matches [{plugin_type}][{plugin_id}][{instance_id}]")
        return filtered

    def to_list(self) -> List[Fixture]:
        """Order the fixtures based on priority.

        This is usefull if you need a list, but you can rely on the
        Fixtures.__iter__ for most scenarios, and just iterate across the
        Fixtures object itself.

        This method is relied on internally.

        Returns:
        --------
        A List[Fixture] of the contained fixtures sorted using their priority.

        """
        return sorted(self._fixtures, key=lambda i: 1 / i.priority if i.priority > 0 else 0)
