"""

DUMMY Plugin testing.

As toolbox operations are quite context sensitive, and could involve creating
infrastructure, we don't have unit testing for them

Here we test the overall toolbox workflows using dummy plugins.

"""
import logging
import unittest

# Configerus imports needed to create a config object
from configerus.contrib.dict import PLUGIN_ID_SOURCE_DICT

# METTA components we will need to access the toolbox
from mirantis.testing.metta import new_environment, environment_names, get_environment

# Used for type hinting and config generation
from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.fixtures import Fixtures
from mirantis.testing.metta.provisioner import METTA_PLUGIN_INTERFACE_ROLE_PROVISIONER
from mirantis.testing.metta.client import METTA_PLUGIN_INTERFACE_ROLE_CLIENT
from mirantis.testing.metta.output import METTA_PLUGIN_INTERFACE_ROLE_OUTPUT
from mirantis.testing.metta.workload import METTA_PLUGIN_INTERFACE_ROLE_WORKLOAD
from mirantis.testing.metta_common.text_output import METTA_PLUGIN_ID_OUTPUT_TEXT
from mirantis.testing.metta_common.dict_output import METTA_PLUGIN_ID_OUTPUT_DICT

# imports used only for type testing
from mirantis.testing.metta_dummy import (
    METTA_PLUGIN_ID_DUMMY_PROVISIONER,
    METTA_PLUGIN_ID_DUMMY_CLIENT,
    METTA_PLUGIN_ID_DUMMY_WORKLOAD,
)
from mirantis.testing.metta_dummy.provisioner import DummyProvisionerPlugin
from mirantis.testing.metta_dummy.client import DummyClientPlugin
from mirantis.testing.metta_dummy.workload import DummyWorkloadPlugin

logger = logging.getLogger("test_dummy")
logger.setLevel(logging.INFO)


CONFIG_DATA = {
    "jsonschema": {
        "plugin": {
            "type": "object",
            "properties": {
                "plugin_id": {"type": "string"},
            },
        }
    },
    "fixtures": {
        "prov1": {
            "plugin_id": METTA_PLUGIN_ID_DUMMY_PROVISIONER,
            "arguments": {
                # Dummy provisioner fixtures
                "fixtures": {
                    # 1. A dummy client fixture that holds 2 dummy outputs
                    "prov1-client1": {
                        "plugin_id": METTA_PLUGIN_ID_DUMMY_CLIENT,
                        "arguments": {
                            "fixtures": {
                                # 1.a. First client output is a dummy text
                                "prov1-client1-output1": {
                                    "plugin_id": METTA_PLUGIN_ID_OUTPUT_TEXT,
                                    "arguments": {
                                        # The text output takes a string 'data'
                                        # constructor argument
                                        "text": "prov client one output one"
                                    },
                                },
                                # 1.b. Second client output is a dummy dict
                                "prov1-client1-output2": {
                                    "plugin_id": METTA_PLUGIN_ID_OUTPUT_DICT,
                                    "arguments": {
                                        # The dict output takes a dict 'data'
                                        # constructor argument
                                        "data": {
                                            "1": {
                                                "1": "prov client one output two data one.one"
                                            }
                                        }
                                    },
                                },
                            }
                        },
                    },
                    # 2. Dummy text output
                    "prov1-output1": {
                        "plugin_id": METTA_PLUGIN_ID_OUTPUT_TEXT,
                        "arguments": {"text": "prov dummy output one"},
                    },
                }
            },
        },
        "work1": {
            "plugin_id": METTA_PLUGIN_ID_DUMMY_WORKLOAD,
        },
        "work2": {
            "plugin_id": METTA_PLUGIN_ID_DUMMY_WORKLOAD,
            "arguments": {
                "fixtures": {
                    "work2-output1": {
                        "plugin_id": METTA_PLUGIN_ID_OUTPUT_TEXT,
                        "arguments": {
                            # The text output takes a string 'data' constructor
                            # argument
                            "text": "workload two dummy output one"
                        },
                    },
                    "work2-client1": {
                        "plugin_id": METTA_PLUGIN_ID_DUMMY_CLIENT,
                    },
                }
            },
        },
    },
}
""" Config for generating dummy plugins

 What is this thing

Well it is a fixtures list which will get passed to add_fixtures_from_config()
on the Environment object.
Plugins are in linear order key=>plugin_definition.

Some plugins/fixtures take 'arguments' which are passed to their constructors.
The Dummy plugins tend to take a 'fixtures' argument which they use to build
more plugins.  This is why it has a deep nested look.

"""


def _dummy_environment() -> Environment:
    """Create an environment object, add the common config source data"""
    if "dummy" not in environment_names():
        logger.info("Creating new environment for DUMMY test suite")
        environment = new_environment(
            name="dummy", additional_metta_bootstraps=["metta_dummy"]
        )
        environment.config.add_source(PLUGIN_ID_SOURCE_DICT).set_data(CONFIG_DATA)

        # this looks magical, but it works because we have structured the
        # fixtures DICT to match expected values properly
        environment.add_fixtures_from_config()

    return get_environment(name="dummy")


def _dummy_provisioner() -> Fixtures:
    """Return a Fixtures of all WORKLOAD plugins"""
    environment = _dummy_environment()
    return environment.fixtures.get(
        interfaces=[METTA_PLUGIN_INTERFACE_ROLE_PROVISIONER]
    ).plugin


def _dummy_workloads() -> Fixtures:
    """Return a Fixtures of all WORKLOAD plugins"""
    environment = _dummy_environment()
    return environment.fixtures.filter(
        interfaces=[METTA_PLUGIN_INTERFACE_ROLE_WORKLOAD]
    )


class DummyTesting(unittest.TestCase):
    """

    Dummy test suite for metta

    """

    def test_dummy_config_basics(self):
        """some sanity testing on the shared config object"""
        environment = _dummy_environment()

        dummy_config = environment.config.load("fixtures")
        self.assertEqual(
            dummy_config.get("prov1.plugin_id"), METTA_PLUGIN_ID_DUMMY_PROVISIONER
        )

        dummy_config.get("work1", validator="jsonschema:plugin")

    def test_provisioner_sanity(self):
        """some sanity testing on loading a provisioner"""
        provisioner = _dummy_provisioner()
        self.assertIsInstance(provisioner, DummyProvisionerPlugin)

    def test_workloads_sanity(self):
        """test that we can load the workloads"""
        workloads = _dummy_workloads()

        workload_one = workloads.get_plugin(instance_id="work1")
        self.assertIsInstance(workload_one, DummyWorkloadPlugin)

        with self.assertRaises(KeyError):
            # pylint: disable=pointless-statement
            workloads["does.not.exist"]

    # pylint: disable=no-self-use
    def test_provisioner_workflow(self):
        """test that the provisioner can follow a decent workflow"""
        provisioner = _dummy_provisioner()

        provisioner.prepare()
        provisioner.apply()

        # ...

        provisioner.destroy()

    def test_workloads_outputs(self):
        """test that the dummy workload got its outputs from configuration"""
        workloads = _dummy_workloads()
        workload_two = workloads.get_plugin(instance_id="work2")

        self.assertEqual(
            workload_two.fixtures.get_plugin(instance_id="work2-output1").get_output(),
            "workload two dummy output one",
        )

    def test_provisioner_outputs(self):
        """test that the provisioner produces the needed clients"""
        provisioner = _dummy_provisioner()
        provisioner.prepare()

        # check that we can get an output from a provisioner
        provisioner_output_dummy = provisioner.fixtures.get_plugin(
            instance_id="prov1-output1"
        )
        self.assertEqual(provisioner_output_dummy.get_output(), "prov dummy output one")

        # make sure that an error is raised if the key doesn't exist
        with self.assertRaises(KeyError):
            provisioner.fixtures.get_plugin(instance_id="does not exist")

    def test_provisioner_clients(self):
        """test that the provisioner produces the needed clients"""
        provisioner = _dummy_provisioner()
        provisioner.prepare()

        # two ways to get the same client in this case
        client_one = provisioner.fixtures.get_plugin(instance_id="prov1-client1")
        self.assertIsInstance(client_one, DummyClientPlugin)
        self.assertEqual(client_one.instance_id, "prov1-client1")
        client_dummy = provisioner.fixtures.get_plugin(
            plugin_id=METTA_PLUGIN_ID_DUMMY_CLIENT
        )
        self.assertIsInstance(client_dummy, DummyClientPlugin)
        self.assertEqual(client_dummy.instance_id, "prov1-client1")

        # make sure that an error is raised if the key doesn't exist
        with self.assertRaises(KeyError):
            provisioner.fixtures.get_plugin(plugin_id="does not exist")

    def test_clients(self):
        """test that the provisioner clients behave like clients"""
        provisioner = _dummy_provisioner()
        provisioner.prepare()

        client_one = provisioner.fixtures.get_plugin(instance_id="prov1-client1")
        self.assertIsInstance(client_one, DummyClientPlugin)

        # test that the dummy plugin can load a text output
        client_one_output = client_one.fixtures.get_plugin(
            instance_id="prov1-client1-output1"
        )
        self.assertEqual(client_one_output.get_output(), "prov client one output one")

        # test that the dummy plugin can load a dict output
        client_two_output = client_one.fixtures.get_plugin(
            instance_id="prov1-client1-output2"
        )
        # Test dict as a loaded config plugin
        self.assertEqual(
            client_two_output.get_output("1.1"),
            "prov client one output two data one.one",
        )
