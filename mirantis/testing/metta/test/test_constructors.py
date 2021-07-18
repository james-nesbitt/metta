"""

DUMMY Plugin testing.

As toolbox operations are quite context sensitive, and could involve creating
infrastructure, we don't have unit testing for them

Here we test the overall toolbox workflows using dummy plugins.

"""
import logging
import unittest

from configerus.contrib.dict import PLUGIN_ID_SOURCE_DICT

# METTA components we will need to access the toolbox
from mirantis.testing.metta import new_environment, environment_names, get_environment

# METTA components for registering plugins
from mirantis.testing.metta.plugin import Factory

# Imports used for type hinting
from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.fixtures import (
    Fixtures,
    METTA_FIXTURES_CONFIG_FIXTURES_LABEL,
)

# imports used only for config creation for testing
from mirantis.testing.metta.provisioner import (
    METTA_PLUGIN_INTERFACE_ROLE_PROVISIONER,
    METTA_PROVISIONER_CONFIG_PROVISIONERS_LABEL,
    METTA_PROVISIONER_CONFIG_PROVISIONER_LABEL,
)
from mirantis.testing.metta.client import (
    METTA_PLUGIN_INTERFACE_ROLE_CLIENT,
    METTA_CLIENT_CONFIG_CLIENTS_LABEL,
    METTA_CLIENT_CONFIG_CLIENT_LABEL,
)
from mirantis.testing.metta.workload import (
    METTA_PLUGIN_INTERFACE_ROLE_WORKLOAD,
    METTA_WORKLOAD_CONFIG_WORKLOADS_LABEL,
    METTA_WORKLOAD_CONFIG_WORKLOAD_LABEL,
)


logger = logging.getLogger("test_dummy")
logger.setLevel(logging.INFO)

# Register some plugins
class GenericTestPlugin:
    """A generic plugin class for various roles."""

    def __init__(self, environment: Environment, instance_id: str, *args, **kwargs):
        """Track the environment and instance_id."""
        self._environment = environment
        self._instance_id = instance_id
        self.args = args
        self.kwargs = kwargs


TEST_PLUGIN_ID_PROVISIONER: str = "test_provisioner"


@Factory(
    plugin_id=TEST_PLUGIN_ID_PROVISIONER,
    interfaces=[METTA_PLUGIN_INTERFACE_ROLE_PROVISIONER],
)
def test_plugin_workload(environment: Environment, instance_id: str, *args, **kwargs):
    """generate a generic plugin which thinks it is a workload plugin."""
    return GenericTestPlugin(
        environment=Environment, instance_id=instance_id, args=args, kwargs=kwargs
    )


TEST_PLUGIN_ID_CLIENT: str = "test_client"


@Factory(plugin_id=TEST_PLUGIN_ID_CLIENT, interfaces=[METTA_PLUGIN_INTERFACE_ROLE_CLIENT])
def test_plugin_workload(environment: Environment, instance_id: str, *args, **kwargs):
    """generate a generic plugin which thinks it is a workload plugin."""
    return GenericTestPlugin(
        environment=Environment, instance_id=instance_id, args=args, kwargs=kwargs
    )


TEST_PLUGIN_ID_WORKLOAD: str = "test_workload"


@Factory(plugin_id=TEST_PLUGIN_ID_WORKLOAD, interfaces=[METTA_PLUGIN_INTERFACE_ROLE_WORKLOAD])
def test_plugin_workload(environment: Environment, instance_id: str, *args, **kwargs):
    """generate a generic plugin which thinks it is a workload plugin."""
    return GenericTestPlugin(
        environment=Environment, instance_id=instance_id, args=args, kwargs=kwargs
    )


# central environment accessor


def _dummy_environment(name: str) -> Environment:
    """Create an environment object, add the common config source data"""
    if name not in environment_names():
        new_environment(name=name, additional_metta_bootstraps=[])

    return get_environment(name=name)


class PluginConstruction(unittest.TestCase):
    """

    Plugin construction test suite

    Test that we can create new plugins using various conditions.  We only create dummy plugins, but
    that tests a lot of the plumbing around plugin registration and configuration.

    """

    def test_1_construct_dicts(self):
        """some sanity tests on constructors based on dicts"""
        environment = _dummy_environment("test_1")

        self.assertIsInstance(
            environment.add_fixture_from_dict(
                plugin_dict={
                    "plugin_id": TEST_PLUGIN_ID_PROVISIONER,
                }
            ).plugin,
            GenericTestPlugin,
        )
        self.assertIsInstance(
            environment.add_fixture_from_dict(
                plugin_dict={
                    "plugin_id": TEST_PLUGIN_ID_CLIENT,
                }
            ).plugin,
            GenericTestPlugin,
        )
        self.assertIsInstance(
            environment.add_fixture_from_dict(
                plugin_dict={
                    "plugin_id": TEST_PLUGIN_ID_WORKLOAD,
                }
            ).plugin,
            GenericTestPlugin,
        )

    def test_2_construct_config(self):
        """test that we can construct plugins from config"""
        environment = _dummy_environment("test_2")

        plugin_dict = {
            "plugin_id": TEST_PLUGIN_ID_CLIENT,
        }
        plugins_dict = {
            "one": {
                "plugin_id": TEST_PLUGIN_ID_CLIENT,
            },
            "two": {
                "plugin_id": TEST_PLUGIN_ID_CLIENT,
            },
            "three": {
                "plugin_id": TEST_PLUGIN_ID_CLIENT,
            },
        }

        environment.config.add_source(PLUGIN_ID_SOURCE_DICT, priority=80).set_data(
            {
                # Group fixture definitions by role
                METTA_PROVISIONER_CONFIG_PROVISIONERS_LABEL: {
                    "one": {
                        "plugin_id": TEST_PLUGIN_ID_PROVISIONER,
                    },
                    "two": {
                        "plugin_id": TEST_PLUGIN_ID_PROVISIONER,
                    },
                    "three": {
                        "plugin_id": TEST_PLUGIN_ID_PROVISIONER,
                    },
                },
                METTA_CLIENT_CONFIG_CLIENTS_LABEL: {
                    "one": {
                        "plugin_id": TEST_PLUGIN_ID_CLIENT,
                    },
                    "two": {
                        "plugin_id": TEST_PLUGIN_ID_CLIENT,
                    },
                    "three": {
                        "plugin_id": TEST_PLUGIN_ID_CLIENT,
                    },
                },
                METTA_WORKLOAD_CONFIG_WORKLOADS_LABEL: {
                    "one": {
                        "plugin_id": TEST_PLUGIN_ID_WORKLOAD,
                    },
                    "two": {
                        "plugin_id": TEST_PLUGIN_ID_WORKLOAD,
                    },
                    "three": {
                        "plugin_id": TEST_PLUGIN_ID_WORKLOAD,
                    },
                },
                # Individual fixture definitions
                METTA_PROVISIONER_CONFIG_PROVISIONER_LABEL: {
                    "plugin_id": TEST_PLUGIN_ID_PROVISIONER,
                },
                METTA_CLIENT_CONFIG_CLIENT_LABEL: {
                    "plugin_id": TEST_PLUGIN_ID_CLIENT,
                },
                METTA_WORKLOAD_CONFIG_WORKLOAD_LABEL: {
                    "plugin_id": TEST_PLUGIN_ID_WORKLOAD,
                },
            }
        )

        self.assertIsInstance(
            environment.add_fixture_from_config(
                label=METTA_PROVISIONER_CONFIG_PROVISIONER_LABEL,
            ).plugin,
            GenericTestPlugin,
        )
        self.assertIsInstance(
            environment.add_fixture_from_config(
                label=METTA_CLIENT_CONFIG_CLIENT_LABEL,
            ).plugin,
            GenericTestPlugin,
        )
        self.assertIsInstance(
            environment.add_fixture_from_config(
                label=METTA_WORKLOAD_CONFIG_WORKLOAD_LABEL,
            ).plugin,
            GenericTestPlugin,
        )

        provisioners = environment.add_fixtures_from_config(
            label=METTA_PROVISIONER_CONFIG_PROVISIONERS_LABEL,
        )

        self.assertIsInstance(provisioners, Fixtures)
        self.assertEqual(len(provisioners), 3)

        two = provisioners.get_plugin(instance_id="two")

        self.assertIsInstance(two, GenericTestPlugin)
        self.assertEqual(
            provisioners.get_plugin(
                interfaces=[METTA_PLUGIN_INTERFACE_ROLE_PROVISIONER]
            ).instance_id,
            "one",
        )

    def test_3_mixedfixtures_flat(self):
        """test building mixed fixtures from one config"""
        environment = _dummy_environment("test_3")

        source = environment.config.add_source(
            PLUGIN_ID_SOURCE_DICT, instance_id="fixtures", priority=80
        )
        source.set_data(
            {
                "fixtures": {
                    "prov": {
                        "plugin_id": TEST_PLUGIN_ID_PROVISIONER,
                    },
                    "cl1": {
                        "plugin_id": TEST_PLUGIN_ID_CLIENT,
                    },
                    "cl2": {
                        "plugin_id": TEST_PLUGIN_ID_CLIENT,
                    },
                    "work1": {
                        "plugin_id": TEST_PLUGIN_ID_WORKLOAD,
                        "priority": environment.plugin_priority() - 10,
                    },
                    "work2": {
                        "plugin_id": TEST_PLUGIN_ID_WORKLOAD,
                        "priority": environment.plugin_priority() + 10,
                    },
                    "work3": {
                        "plugin_id": TEST_PLUGIN_ID_WORKLOAD,
                    },
                },
            }
        )

        environment.add_fixtures_from_config(label=METTA_FIXTURES_CONFIG_FIXTURES_LABEL)

        cl2 = environment.fixtures.get_plugin(instance_id="cl2")
        self.assertEqual(cl2.instance_id, "cl2")

        wls = environment.fixtures.filter(interfaces=[METTA_PLUGIN_INTERFACE_ROLE_WORKLOAD])

        self.assertEqual(len(wls), 3)

        wl2 = wls.get(instance_id="work2")
        self.assertEqual(wl2.plugin.instance_id, "work2")
        self.assertEqual(wl2, wls["work2"])
        wl1 = wls.get_plugin(instance_id="work1")
        self.assertEqual(wl1.instance_id, "work1")
        self.assertEqual(wl1, wls["work1"].plugin)
