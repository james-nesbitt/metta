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

# We import this so that we don't need to guess on plugin_ids, but not needed
from mirantis.testing.metta_dummy import METTA_PLUGIN_ID_DUMMY

# Imports used for type hinting
from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.fixtures import (
    Fixtures,
    METTA_FIXTURES_CONFIG_FIXTURES_LABEL,
)

# imports used only for config creation for testing
from mirantis.testing.metta.provisioner import (
    METTA_PLUGIN_TYPE_PROVISIONER,
    METTA_PROVISIONER_CONFIG_PROVISIONERS_LABEL,
    METTA_PROVISIONER_CONFIG_PROVISIONER_LABEL,
)
from mirantis.testing.metta.client import (
    METTA_PLUGIN_TYPE_CLIENT,
    METTA_CLIENT_CONFIG_CLIENTS_LABEL,
    METTA_CLIENT_CONFIG_CLIENT_LABEL,
)
from mirantis.testing.metta.workload import (
    METTA_PLUGIN_TYPE_WORKLOAD,
    METTA_WORKLOAD_CONFIG_WORKLOADS_LABEL,
    METTA_WORKLOAD_CONFIG_WORKLOAD_LABEL,
)

# imports used only for type testing
from mirantis.testing.metta_dummy.provisioner import DummyProvisionerPlugin
from mirantis.testing.metta_dummy.client import DummyClientPlugin
from mirantis.testing.metta_dummy.workload import DummyWorkloadPlugin

logger = logging.getLogger("test_dummy")
logger.setLevel(logging.INFO)


def _dummy_environment(name: str) -> Environment:
    """Create an environment object, add the common config source data"""
    if name not in environment_names():
        new_environment(name=name, additional_metta_bootstraps=["metta_dummy"])

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

        plugin_dict = {
            "plugin_id": METTA_PLUGIN_ID_DUMMY,
        }

        self.assertIsInstance(
            environment.add_fixture_from_dict(
                plugin_type=METTA_PLUGIN_TYPE_PROVISIONER, plugin_dict=plugin_dict
            ).plugin,
            DummyProvisionerPlugin,
        )
        self.assertIsInstance(
            environment.add_fixture_from_dict(
                plugin_type=METTA_PLUGIN_TYPE_CLIENT, plugin_dict=plugin_dict
            ).plugin,
            DummyClientPlugin,
        )
        self.assertIsInstance(
            environment.add_fixture_from_dict(
                plugin_type=METTA_PLUGIN_TYPE_WORKLOAD, plugin_dict=plugin_dict
            ).plugin,
            DummyWorkloadPlugin,
        )

        plugins_dict = {
            "one": plugin_dict,
            "two": plugin_dict,
            "three": plugin_dict,
        }
        provisioners = environment.add_fixtures_from_dict(
            plugin_type=METTA_PLUGIN_TYPE_PROVISIONER, plugin_list=plugins_dict
        )

        self.assertIsInstance(provisioners, Fixtures)
        self.assertEqual(len(provisioners), 3)

        one = provisioners.get_plugin(instance_id="one")
        two = provisioners.get_plugin(instance_id="two")

        self.assertIsInstance(one, DummyProvisionerPlugin)
        self.assertIsInstance(two, DummyProvisionerPlugin)
        self.assertEqual(
            provisioners.get_plugin(
                plugin_type=METTA_PLUGIN_TYPE_PROVISIONER
            ).instance_id,
            "one",
        )
        self.assertEqual(
            provisioners.get_plugin(plugin_type=METTA_PLUGIN_TYPE_PROVISIONER), one
        )

    def test_2_construct_config(self):
        """test that we can construct plugins from config"""
        environment = _dummy_environment("test_2")

        plugin_dict = {
            "plugin_id": METTA_PLUGIN_ID_DUMMY,
        }
        plugins_dict = {
            "one": plugin_dict,
            "two": plugin_dict,
            "three": plugin_dict,
        }

        environment.config.add_source(PLUGIN_ID_SOURCE_DICT, priority=80).set_data(
            {
                METTA_PROVISIONER_CONFIG_PROVISIONERS_LABEL: plugins_dict,
                METTA_CLIENT_CONFIG_CLIENTS_LABEL: plugins_dict,
                METTA_WORKLOAD_CONFIG_WORKLOADS_LABEL: plugins_dict,
                METTA_PROVISIONER_CONFIG_PROVISIONER_LABEL: plugin_dict,
                METTA_CLIENT_CONFIG_CLIENT_LABEL: plugin_dict,
                METTA_WORKLOAD_CONFIG_WORKLOAD_LABEL: plugin_dict,
            }
        )

        self.assertIsInstance(
            environment.add_fixture_from_config(
                plugin_type=METTA_PLUGIN_TYPE_PROVISIONER,
                label=METTA_PROVISIONER_CONFIG_PROVISIONER_LABEL,
            ).plugin,
            DummyProvisionerPlugin,
        )
        self.assertIsInstance(
            environment.add_fixture_from_config(
                plugin_type=METTA_PLUGIN_TYPE_CLIENT,
                label=METTA_CLIENT_CONFIG_CLIENT_LABEL,
            ).plugin,
            DummyClientPlugin,
        )
        self.assertIsInstance(
            environment.add_fixture_from_config(
                plugin_type=METTA_PLUGIN_TYPE_WORKLOAD,
                label=METTA_WORKLOAD_CONFIG_WORKLOAD_LABEL,
            ).plugin,
            DummyWorkloadPlugin,
        )

        provisioners = environment.add_fixtures_from_config(
            plugin_type=METTA_PLUGIN_TYPE_PROVISIONER,
            label=METTA_PROVISIONER_CONFIG_PROVISIONERS_LABEL,
        )

        self.assertIsInstance(provisioners, Fixtures)
        self.assertEqual(len(provisioners), 3)

        two = provisioners.get_plugin(instance_id="two")

        self.assertIsInstance(two, DummyProvisionerPlugin)
        self.assertEqual(
            provisioners.get_plugin(
                plugin_type=METTA_PLUGIN_TYPE_PROVISIONER
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
                        "plugin_type": METTA_PLUGIN_TYPE_PROVISIONER,
                        "plugin_id": METTA_PLUGIN_ID_DUMMY,
                    },
                    "cl1": {
                        "plugin_type": METTA_PLUGIN_TYPE_CLIENT,
                        "plugin_id": METTA_PLUGIN_ID_DUMMY,
                    },
                    "cl2": {
                        "plugin_type": METTA_PLUGIN_TYPE_CLIENT,
                        "plugin_id": METTA_PLUGIN_ID_DUMMY,
                    },
                    "work1": {
                        "plugin_type": METTA_PLUGIN_TYPE_WORKLOAD,
                        "plugin_id": METTA_PLUGIN_ID_DUMMY,
                        "priority": environment.plugin_priority() - 10,
                    },
                    "work2": {
                        "plugin_type": METTA_PLUGIN_TYPE_WORKLOAD,
                        "plugin_id": METTA_PLUGIN_ID_DUMMY,
                        "priority": environment.plugin_priority() + 10,
                    },
                    "work3": {
                        "plugin_type": METTA_PLUGIN_TYPE_WORKLOAD,
                        "plugin_id": METTA_PLUGIN_ID_DUMMY,
                    },
                },
            }
        )

        environment.add_fixtures_from_config(label=METTA_FIXTURES_CONFIG_FIXTURES_LABEL)

        cl2 = environment.fixtures.get_plugin(
            plugin_type=METTA_PLUGIN_TYPE_CLIENT, instance_id="cl2"
        )
        self.assertEqual(cl2.instance_id, "cl2")

        wls = environment.fixtures.filter(plugin_type=METTA_PLUGIN_TYPE_WORKLOAD)

        self.assertEqual(len(wls), 3)
        self.assertEqual(wls[0].plugin.instance_id, "work2")
        self.assertEqual(wls[2].plugin.instance_id, "work1")
