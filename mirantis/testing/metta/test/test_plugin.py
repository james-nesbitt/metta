"""

Unit test for the plugin functionality.

Run plugin registry, and confirm that registraion was succesful and that
registered plugins can be created, and that features are registered
properly.

"""

from typing import List
import unittest

from mirantis.testing.metta.plugin import Factory


class TestPlugin:
    """Test class used to test registration."""

    def __init__(self, testcase):
        """Assign testcase."""
        self.testcase = testcase


class TestPluginRegistration(unittest.TestCase):
    """Test plugin registration."""

    def test_plugin_ids_and_interfaces(self):
        """Test that our plugin id was registered."""

        plugin_id: str = "test_register"
        plugin_interfaces: List[str] = ["test", "register"]

        @Factory(plugin_id=plugin_id, interfaces=plugin_interfaces)
        def my_test_plugin_factory(testcase):
            """Inline disposable factory."""
            return TestPlugin(testcase)

        self.assertIn(plugin_id, Factory.plugin_ids())

        plugin_interfaces = Factory.interfaces()
        for plugin_interface in plugin_interfaces:
            self.assertIn(plugin_interface, plugin_interfaces)

    def test_no_id_duplicates_allowed(self):
        """Assert that we get an error if we try to dupe ids."""
        plugin_id: str = "test_duplicates"
        plugin_interfaces: List[str] = []

        @Factory(plugin_id=plugin_id, interfaces=plugin_interfaces)
        def factory_1(testcase):
            """Inline disposable factory."""
            return TestPlugin(testcase)

        with self.assertRaises(KeyError):

            @Factory(plugin_id=plugin_id, interfaces=plugin_interfaces)
            def factory_2(testcase):
                """Inline disposable factory."""
                return TestPlugin(testcase)


class TestPluginCreation(unittest.TestCase):
    """Test plugin registration."""

    def test_plugin_create(self):
        """Test that we can run a plugin decorating registration."""

        plugin_id: str = "test_registration"
        plugin_interfaces: List[str] = ["test", "registration"]

        @Factory(plugin_id=plugin_id, interfaces=plugin_interfaces)
        def my_test_plugin_factory(testcase):
            """Inline disposable factory."""
            return TestPlugin(testcase)

        instance_id = "test_plugin_create"
        instance = Factory.create(plugin_id=plugin_id, instance_id=instance_id, testcase=self)

        self.assertEqual(instance.instance_id, instance_id)
        for plugin_interface in plugin_interfaces:
            self.assertIn(plugin_interface, instance.interfaces)

        plugin = instance.plugin

        self.assertEqual(plugin.testcase, self)


class test_plugin_interface_filter(unittest.TestCase):
    """Test that filtering plugin_id by feature works."""

    def test_interface_filter(self):
        """Test that we can run a plugin decorating registration."""

        # register plugins with interfaces that we will search for
        @Factory(plugin_id=f"test_1", interfaces=["1", "2"])
        def my_test_plugin_factory(testcase):
            """Inline disposable factory."""
            return TestPlugin(testcase)

        @Factory(plugin_id=f"test_2", interfaces=["1", "2", "3"])
        def my_test_plugin_factory(testcase):
            """Inline disposable factory."""
            return TestPlugin(testcase)

        @Factory(plugin_id=f"test_3", interfaces=["2", "3"])
        def my_test_plugin_factory(testcase):
            """Inline disposable factory."""
            return TestPlugin(testcase)

        ids_all = Factory.plugin_ids()
        self.assertIn("test_1", ids_all)
        self.assertIn("test_2", ids_all)
        self.assertIn("test_3", ids_all)
        ids_for_1 = Factory.plugin_ids(interfaces_filter=["1"])
        self.assertIn("test_1", ids_for_1)
        self.assertIn("test_2", ids_for_1)
        self.assertNotIn("test_3", ids_for_1)
        ids_for_2 = Factory.plugin_ids(interfaces_filter=["2"])
        self.assertIn("test_1", ids_for_2)
        self.assertIn("test_2", ids_for_2)
        self.assertIn("test_3", ids_for_2)
        ids_for_3 = Factory.plugin_ids(interfaces_filter=["3"])
        self.assertNotIn("test_1", ids_for_3)
        self.assertIn("test_2", ids_for_3)
        self.assertIn("test_3", ids_for_3)
