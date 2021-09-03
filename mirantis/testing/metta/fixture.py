"""

Fixture management code.

A Fixture is a plugin instance wrapper that keeps metadata about the plugin
instance.
A Fixtures object is a collection of plugin instances kept as an
ordered, managed set.

A fixture saves us from applying any required interface onto a plugin for
maintaining metadata about the plugin, however, as a wrapper, it also leaves
the plugin in the dark about its own metadata.

## TODO

* Fixtures are now a pivotal cental component in metta, because most of the
  core and contrib functionality is provided by plugins, even bootstrapping
  and environments are plugins.  This means that even the core uses a lot of
  Fixtures searching and managemeng.
  Because of this prevalence, the Fixtures object could use some streamlining
  and optimization for its implementation.
  Some ideas:
    1. low volume (<100) optimization of filtering/searching methods; perhaps
       caching.
    2. optimization of merging and copying?

"""
import logging
from typing import Any, Dict, List, Iterator

# pylint: disable=W0511
# TODO move these to this file as METTA_FIXTURE_KEY_XXXXX
from .plugin import (
    Instance,
    METTA_PLUGIN_CONFIG_KEY_PLUGINID,
    METTA_PLUGIN_CONFIG_KEY_INSTANCEID,
)

logger = logging.getLogger("metta.fixture")

METTA_FIXTURES_CONFIG_FIXTURES_LABEL = "fixtures"
""" A centralized configerus load label for multiple fixtures """
METTA_FIXTURES_CONFIG_FIXTURE_KEY = "fixture"
""" Config .get() key for a single fixture """
METTA_FIXTURE_CONFIG_KEY_PRIORITY = "priority"
""" configerus .get()  assign an instance a priority when it is created. """
METTA_FIXTURE_CONFIG_KEY_CONFIG = "config"
""" configerus .get()  as additional config """
METTA_FIXTURE_CONFIG_KEY_VALIDATORS = "validators"
""" configerus .get()  to decide what validators to apply to the plugin """

METTA_FIXTURE_VALIDATION_JSONSCHEMA = {
    "type": "object",
    "properties": {
        METTA_PLUGIN_CONFIG_KEY_PLUGINID: {"type": "string"},
        METTA_PLUGIN_CONFIG_KEY_INSTANCEID: {"type": "string"},
        METTA_FIXTURE_CONFIG_KEY_PRIORITY: {
            "type": "integer",
            "minimum": 1,
            "maximum": 100,
        },
    },
    "required": [METTA_PLUGIN_CONFIG_KEY_PLUGINID],
}
""" json schema validation definition for a plugin """


class Fixture:
    """A plugin wrapper struct that keep metadata about the plugin in a set.

    A Fixture is yet another wrapper for a plugin object which contains
    metadata about the plugin.  This is similar to the plugin.PluginInstance
    wrapper, but it also adds a priority intereger for relative importance.

    """

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        plugin: Any,
        plugin_id: str,
        instance_id: str,
        interfaces: List[str],
        labels: Dict[str, str],
        priority: int,
    ):
        """Initialize struct contents.

        Parameters:
        -----------
        plugin : the fixture plugin instance

        Filtering parameters:

        plugin_id (str) : registry plugin_id
        instance_id (str) : plugin instance identifier
        interfaces (list[str]) : string list of interface
            identifiers that the plugin should support.

        """
        self.plugin_id: str = plugin_id
        self.instance_id: str = instance_id
        self.interfaces: List[str] = interfaces
        self.labels: Dict[str, str] = labels
        self.priority: int = priority
        self.plugin: Any = plugin

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

        return self.plugin_id == other.plugin_id and self.instance_id == other.instance_id

    def info(self, deep: bool = False, children: bool = False) -> Dict[str, Any]:
        """Return some dict metadata about the fixture and plugin.

        Parameters:
        -----------
        deep (bool) : whether or not the information provided should go deep
            into the avaiable sources of data.  Info is intended to be cheap
            to perform, but there are some scenarios where you want more data
            despite the cost, or risk for exception.
        children (bool) : if the fixture has children fixtures, then this
            flag controls whether or not the children info should also be
            included.

        Returns:
        --------
        Dict[str, Any] or primitives that can be used for introspection of the
        fixtures.

        Raises:
        -------
        Info() should be safe for operation, but if deep=True then there may be
        a risk of a plugin throwing an exception.

        """
        fixture_info: Dict[str, Any] = {
            "fixture": {
                "instance_id": self.instance_id,
                "plugin_id": self.plugin_id,
                "interfaces": self.interfaces,
                "labels": self.labels,
                "priority": self.priority,
            }
        }
        # If a plugin has a callable info method then add it to the info
        if hasattr(self.plugin, "info"):
            fixture_info["plugin"] = self.plugin.info(deep=deep)
        # if the plugin hsa child, optionally add their info
        if children and hasattr(self.plugin, "fixtures") and callable(self.plugin.fixtures):
            fixture_info["fixtures"] = {}
            for fixture in self.plugin.fixtures():
                fixture_info["fixtures"][fixture.instance_id] = fixture.info(
                    deep=deep, children=children
                )

        return fixture_info

    def has_interfaces(self, interfaces: List[str]) -> bool:
        """Does this fixture have all of the passed interfaces."""
        for required_interface in interfaces:
            if required_interface not in self.interfaces:
                return False
        return True

    def has_labels(self, labels: List[str]) -> bool:
        """Does this fixture have all of the passed labels."""
        for required_label in labels:
            if required_label not in self.labels.keys():
                return False
        return True

    @classmethod
    def from_instance(
        cls, instance: Instance, priority: int, labels: Dict[str, str] = None
    ) -> "Fixture":
        """Convert a plugin instance to a fixture."""
        # Labels are merged from the plugin instance and the passed in fixture overrides.
        if labels is None:
            labels = {}
        if instance.labels is not None:
            labels_copy = instance.labels.copy()
            labels_copy.update(labels)
            labels = labels_copy

        return cls(
            plugin_id=instance.plugin_id,
            instance_id=instance.instance_id,
            interfaces=instance.interfaces,
            labels=labels,
            priority=priority,
            plugin=instance.plugin,
        )


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

    def __getitem__(self, instance_id: str):
        """Subscribe to a fixtures instance using instance_id.

        Parameters:
        -----------
        instance_id (str) : fixture instance_id you are looking for.

        Returns:
        --------
        A Fixture object with the passed instance_id.

        Raises:
        -------
        Will raise a KeyError if the instance_id does not exist in the set. the
        exception is actually raised by the .get() method.

        """
        return self.get(instance_id=instance_id)

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

    def info(self, deep: bool = False) -> Dict[str, Any]:
        """Return some dict metadata about the fixtures and plugins."""
        fixtures_info: Dict[str, Any] = {}
        for fixture in self._fixtures:
            fixtures_info[fixture.instance_id] = fixture.info(deep=deep)

        return fixtures_info

    def merge(self, merge_from: "Fixtures"):
        """Merge fixture instances from another Fixtures object into this one.

        Parameters:
        -----------
        Merge_from (Fixtures) : fixture instance source

        Raises:
        -------
        May raise a KeyError if there a matching plugin is already in the
        Fixtures object.

        """
        # We use the add_fixture method to centralize the logic for adding fixtures to one function
        for fixture in merge_from:
            self.add(fixture)

    # pylint: disable=too-many-arguments
    def new(
        self,
        plugin: object,
        plugin_id: str,
        instance_id: str,
        interfaces: List[str],
        labels: Dict[str, str],
        priority: int,
        replace_existing: bool = False,
    ) -> Fixture:
        """Add a new fixture by providing the plugin instance and the metadata.

        Create a new Fixture from the passed arguments and add it to the
        Fixtures set.

        Parameters:
        -----------
        plugin : the fixture plugin instance

        Filtering parameters:

        plugin_id (str) : registry plugin_id
        instance_id (str) : plugin instance identifier
        interfaces (List[str]) : interface identifiers supported
        labels: [str, str] : labels for the instance
        priority (int) : plugin priority

        """
        return self.add(
            Fixture(
                plugin_id=plugin_id,
                instance_id=instance_id,
                priority=priority,
                interfaces=interfaces,
                labels=labels,
                plugin=plugin,
            ),
            replace_existing=replace_existing,
        )

    def add(self, fixture: Fixture, replace_existing: bool = False) -> Fixture:
        """Add an existing fixture.

        If a matching

        Parameters:
        -----------
        fixture (Fixture) : existing fixture to add

        replace_existing (bool) : If True, then this fixture can replace a
            matching plugin with the same metadata.

        """
        if self.get(
            plugin_id=fixture.plugin_id,
            instance_id=fixture.instance_id,
            exception_if_missing=False,
        ):

            if not replace_existing:
                raise KeyError(
                    "Fixture index already exists:"
                    f"[plugin_id:{fixture.plugin_id}]"
                    f"[instance_id:{fixture.instance_id}]"
                )

            # array index needed for replacement
            # pylint: disable=consider-using-enumerate
            for i in range(len(self._fixtures)):
                if self._fixtures[i] == fixture:
                    self._fixtures[i] = fixture
                    return fixture

        self._fixtures.append(fixture)

        return fixture

    def get(
        self,
        plugin_id: str = "",
        instance_id: str = "",
        interfaces: List[str] = None,
        labels: Dict[str, str] = None,
        has_labels: List[str] = None,
        exception_if_missing: bool = True,
    ) -> Fixture:
        """Retrieve the first matching fixture object based on filters and priority.

        Parameters:
        -----------
        Filtering parameters:

        plugin_id (str) : registry plugin_id
        instance_id (str) : plugin instance identifier
        interfaces (List[str]) : List of interfaces which the fixture must have
        labels (Dict[str, str]) : Filter key value pairs which fixtures must match
        has_labels (List[str]) : List of labels which the fixture must have

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
            plugin_id=plugin_id,
            instance_id=instance_id,
            interfaces=interfaces,
            labels=labels,
            has_labels=has_labels,
        )

        if len(filtered) > 0:
            return filtered.to_list()[0]
        if exception_if_missing:
            raise KeyError(
                "Could not find any matching fixture instances "
                f"[plugin_id:{plugin_id}][instance_id:{instance_id}]"
                f"[interfaces:{interfaces}][labels:{labels}]"
            )
        # filtered list was empty, and we were not directed to raise an exception for that.
        return None

    def get_plugin(
        self,
        plugin_id: str = "",
        instance_id: str = "",
        interfaces: List[str] = None,
        labels: Dict[str, str] = None,
        has_labels: List[str] = None,
        exception_if_missing: bool = True,
    ) -> object:
        """Retrieve the first matching plugin  based on filters and priority.

        Parameters:
        -----------
        Filtering parameters:

        plugin_id (str) : registry plugin_id
        interfaces (List[str]) : List of interfaces which the fixture must have
        labels (Dict[str, str]) : Filter key value pairs which fixtures must match
        has_labels (List[str]) : List of labels which the fixture must have
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
            plugin_id=plugin_id,
            instance_id=instance_id,
            interfaces=interfaces,
            labels=labels,
            has_labels=has_labels,
            exception_if_missing=exception_if_missing,
        )

        if fixture is None:
            return None
        return fixture.plugin

    # I should try to fix the branch count here
    # pylint: disable=too-many-branches
    def filter(
        self,
        plugin_id: str = "",
        instance_id: str = "",
        interfaces: List[str] = None,
        labels: Dict[str, str] = None,
        has_labels: List[str] = None,
        exception_if_missing: bool = False,
    ) -> "Fixtures":
        """Filter the fixture instances.

        Parameters:
        -----------
        Filtering parameters:

        plugin_id (str) : registry plugin_id
        interfaces (List[str]) : List of interfaces which the fixture must have
        labels (Dict[str, str]) : Filter key value pairs which fixtures must match
        has_labels (List[str]) : List of labels which the fixture must have
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
            try:
                if interfaces:
                    for required_interface in interfaces:
                        if required_interface not in fixture.interfaces:
                            raise DoesNotMatchError("does not contain required interface")

                if has_labels:
                    for required_label in has_labels:
                        if required_label not in fixture.labels:
                            raise DoesNotMatchError("does not contain required label")

                if labels:
                    for key, value in labels.items():
                        if key not in fixture.labels:
                            raise DoesNotMatchError("does not contain required label")
                        if not fixture.labels[key] == value:
                            raise DoesNotMatchError("required label does not match")

                if plugin_id and not fixture.plugin_id == plugin_id:
                    raise DoesNotMatchError("plugin_id does not match")
                if instance_id and not fixture.instance_id == instance_id:
                    raise DoesNotMatchError("instance_id does not match")

                filtered.add(fixture, replace_existing=True)

            except DoesNotMatchError:
                pass

        if exception_if_missing and len(filtered) == 0:
            raise KeyError(f"Filter found matches [{plugin_id}][{instance_id}]")
        return filtered

    def filter_out(
        self,
        plugin_id: str = "",
        instance_id: str = "",
        interfaces: List[str] = None,
        labels: Dict[str, str] = None,
        has_labels: List[str] = None,
        exception_if_missing: bool = False,
    ) -> "Fixtures":
        """Return the fixtures with fixtures removed.

        Parameters:
        -----------
        Filtering parameters:

        plugin_id (str) : registry plugin_id
        interfaces (List[str]) : List of interfaces which the fixture must have
        labels (List[str]) : List of labels which the fixture must have
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
            try:
                if interfaces:
                    for required_interface in interfaces:
                        if required_interface not in fixture.interfaces:
                            raise DoesNotMatchError("does not contain required interface")

                if has_labels:
                    for required_label in has_labels:
                        if required_label not in fixture.labels:
                            raise DoesNotMatchError("does not contain required label")

                if labels:
                    for key, value in labels.items():
                        if key not in fixture.labels:
                            raise DoesNotMatchError("does not contain required label")
                        if not fixture.labels[key] == value:
                            raise DoesNotMatchError("required label does not match")

                if plugin_id and not fixture.plugin_id == plugin_id:
                    raise DoesNotMatchError("plugin_id does not match")

                if instance_id and not fixture.instance_id == instance_id:
                    raise DoesNotMatchError("instance_id does not match")

            except DoesNotMatchError:
                filtered.add(fixture, replace_existing=True)

        if exception_if_missing and len(filtered) == 0:
            raise KeyError(f"Filter found matches [{plugin_id}][{instance_id}]")
        return filtered

    def to_list(self) -> List[Fixture]:
        """Order the fixtures based on priority.

        This is usefull if you need a list, but you can rely on the
        Fixtures.__iter__ for most scenarios, and just iterate across the
        Fixtures object itself.

        This method is relied on internally.

        Returns:
        --------
        A List[Fixture] of the contained fixtures sorted using their priority,
        sorted from lowest to highest priority.

        """
        return sorted(self._fixtures, key=lambda i: 1 / i.priority if i.priority > 0 else 100)


class DoesNotMatchError(Exception):
    """An exception to indicate that a value does not match filter expectations."""
