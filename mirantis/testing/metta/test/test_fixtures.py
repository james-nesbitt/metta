"""

Unit testing for fixtures

Test fixtures as extensions of plugin and test the Fixtures 
collection as a tool for managing Fixture objects.

"""

import unittest
from typing import List

from mirantis.testing.metta.plugin import Factory
from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.fixtures import Fixture, Fixtures


##### Register pluging for testing ############################################
class TestPlugin:
    """testing plugin class."""

    def __init__(self, environment: Environment):
        """Attach an environment object to the plugin."""
        self._environment = environment


TEST_PLUGIN_ID: str = "fixture_test"
TEST_PLUGIN_INTERFACES: List[str] = ["dummy"]


@Factory(plugin_id=TEST_PLUGIN_ID, interfaces=TEST_PLUGIN_INTERFACES)
def test_factory(environment: Environment) -> TestPlugin:
    """Create a test plugin object."""


##### Finished registering testing plugin #####################################


class TestFixture(unittest.TestCase):
    """Unit tests for the Fixture object."""

    def test_fixture_make(self):
        """Simply test that we can make and access a fixture from an instance."""
        instance_id = "test_fixture_make"
        mock_environment = self
        priority = 75

        plugin_instance = test_factory(environment=mock_environment)
        fixture = Fixture(
            plugin_id=TEST_PLUGIN_ID,
            instance_id=instance_id,
            priority=priority,
            interfaces=TEST_PLUGIN_INTERFACES,
            plugin=plugin_instance,
        )

        self.assertEqual(fixture.plugin_id, TEST_PLUGIN_ID)
        self.assertEqual(fixture.instance_id, instance_id)
        self.assertEqual(fixture.priority, priority)

        for expected_interface in TEST_PLUGIN_INTERFACES:
            self.assertIn(expected_interface, fixture.interfaces)

        fixture_dup = Fixture(
            plugin_id=TEST_PLUGIN_ID,
            instance_id=instance_id,
            priority=priority,
            interfaces=TEST_PLUGIN_INTERFACES,
            plugin=plugin_instance,
        )

        self.assertEqual(fixture_dup, fixture)

        instance_id_notdupe = "not_a_dupe"
        fixture_notdup = Fixture(
            plugin_id=TEST_PLUGIN_ID,
            instance_id=instance_id_notdupe,
            priority=priority,
            interfaces=TEST_PLUGIN_INTERFACES,
            plugin=plugin_instance,
        )

        self.assertNotEqual(fixture_notdup, fixture)

    def test_fixture_from_fixture(self):
        """Simply test that we can make and access a fixture from an instance."""
        instance_id = "test_fixture_make"
        mock_environment = self
        priority = 75

        plugin_instance = Factory.create(
            plugin_id=TEST_PLUGIN_ID,
            instance_id=instance_id,
            environment=mock_environment,
        )
        fixture = Fixture.from_instance(plugin_instance, priority)

        self.assertEqual(fixture.plugin_id, TEST_PLUGIN_ID)
        self.assertEqual(fixture.instance_id, instance_id)
        self.assertEqual(fixture.priority, priority)

        for expected_interface in TEST_PLUGIN_INTERFACES:
            self.assertIn(expected_interface, fixture.interfaces)


class TestFixtures(unittest.TestCase):
    """Unit testing of the Fixtures class."""

    def _some_fixtures(self):
        """Create some fixtures to test against."""
        fixtures = Fixtures()

        fixtures.new(
            plugin_id="one",
            instance_id="1",
            priority=50,
            interfaces=["A", "B"],
            plugin=None,
        )
        fixtures.new(plugin_id="one", instance_id="2", priority=74, interfaces=["A"], plugin=None)
        fixtures.new(
            plugin_id="two",
            instance_id="2",
            priority=60,
            interfaces=["A", "B"],
            plugin=None,
        )
        fixtures.new(
            plugin_id="two",
            instance_id="3",
            priority=10,
            interfaces=["A", "B", "C"],
            plugin=None,
        )

        return fixtures

    def test_fixtures_adding_merging(self):
        """Test that we can add without error."""
        fixtures = self._some_fixtures()

        with self.assertRaises(KeyError):
            fixtures.new(
                plugin_id="one",
                instance_id="1",
                priority=50,
                interfaces=["A", "B"],
                plugin=None,
            )

    def test_fixtures_fixtures_as_a_set(self):
        """test that the fixtures object behaves as a native set."""
        fixtures = self._some_fixtures()

        self.assertEqual(len(fixtures), 4)

        # the fixtures iterator is supposed to be sorted by priority
        priority = 101
        for fixture in fixtures:
            self.assertLessEqual(fixture.priority, priority)
            priority = fixture.priority
        # fixtures has native reversing
        priority = 0
        for fixture in reversed(fixtures):
            self.assertGreaterEqual(fixture.priority, priority)
            priority = fixture.priority

    def test_fixtures_filter(self):
        """test that the fixtures object behaves as a native set."""
        fixtures = self._some_fixtures()

        filter_plugins = fixtures.filter(plugin_id="one")
        self.assertEqual(len(filter_plugins), 2)
        filter_plugins_list = list(
            filter_plugins
        )  # this is not a good pattern, but it facilitates testing
        self.assertEqual(len(filter_plugins_list), 2)
        # these asserts are based on values for the fixtures
        self.assertEqual(filter_plugins_list[0].plugin_id, "one")
        self.assertEqual(filter_plugins_list[0].instance_id, "2")
        self.assertEqual(filter_plugins_list[1].plugin_id, "one")
        self.assertEqual(filter_plugins_list[1].instance_id, "1")

        filter_interface_B = fixtures.filter(interfaces=["B"])
        self.assertEqual(len(filter_interface_B), 3)
        filter_interface_C = fixtures.filter(interfaces=["C"])
        self.assertEqual(len(filter_interface_C), 1)
        filter_interface_no = fixtures.filter(interfaces=["no"])
        self.assertEqual(len(filter_interface_no), 0)

        filter_instance_2 = fixtures.filter(instance_id="2")
        self.assertEqual(len(filter_instance_2), 2)
        filter_instance_3 = fixtures.filter(instance_id="3")
        self.assertEqual(len(filter_instance_3), 1)
        filter_plugins_list = list(
            filter_instance_3
        )  # this is not a good pattern, but it facilitates testing
        self.assertEqual(filter_plugins_list[0].plugin_id, "two")
        self.assertEqual(filter_plugins_list[0].instance_id, "3")
