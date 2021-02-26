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
from mirantis.testing.metta.plugin import Type
# Used for type hinting
from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.fixtures import Fixtures

# imports used only for type testing
from mirantis.testing.metta_dummy.provisioner import DummyProvisionerPlugin
from mirantis.testing.metta_dummy.client import DummyClientPlugin
from mirantis.testing.metta_dummy.workload import DummyWorkloadPlugin

logger = logging.getLogger("test_dummy")
logger.setLevel(logging.INFO)


""" Config for generating dummy plugins

 What is this thing

Well it is a fixtures list which will get passed to add_fixtures_from_config()
on the Environment object.
Plugins are in linear order key=>plugin_definition.

Some plugins/fixtures take 'arguments' which are passed to their constructors.
The Dummy plugins tend to take a 'fixtures' argument which they use to build
more plugins.  This is why it has a deep nested look.

WHAT WEIRD THINGS HAVE WE DONE:

1. plugin type:  sometimes we use the actual Type.XXXX.value, sometimes a short
        string, and a long string. We need to make sure that all of them work.

"""

CONFIG_DATA = {
    'jsonschema': {
        'plugin': {
            "type": "object",
            "properties": {
                "type": {"type": "string"},
                "plugin_id": {"type": "string"},
            }
        }
    },
    'fixtures': {
        'prov1': {
            'type': 'PROVISIONER',
            'plugin_id': 'dummy',
            'arguments': {
                # Dummy provisioner fixtures
                'fixtures': {
                    # 1. A dummy client fixture that holds 2 dummy outputs
                    'client1': {
                        'type': 'client',
                        'plugin_id': 'dummy',
                        'arguments': {
                            'fixtures': {
                                # 1.a. First client output is a dummy text
                                'output1': {
                                    'type': 'output',
                                    'plugin_id': 'text',
                                    'arguments': {
                                        # The text output takes a string 'data'
                                        # constructor argument
                                        'text': "prov client one output one"
                                    }
                                },
                                # 1.b. Second client output is a dummy dict
                                'output2': {
                                    'type': 'metta.plugin.output',
                                    'plugin_id': 'dict',
                                    'arguments': {
                                        # The dict output takes a dict 'data'
                                        # constructor argument
                                        'data': {
                                            '1': {
                                                '1': "prov client one output two data one.one"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    # 2. Dummy text output
                    'output1': {
                        'type': Type.OUTPUT.value,
                        'plugin_id': 'text',
                        'arguments': {
                            'text': "prov dummy output one"
                        }
                    }
                }
            }
        },
        'work1': {
            'type': Type.WORKLOAD.value,
            'plugin_id': 'dummy',
        },
        'work2': {
            'type': 'workload',
            'plugin_id': 'dummy',
            'arguments': {
                'fixtures': {
                    'output1': {
                        'type': 'output',
                        'plugin_id': 'text',
                        'arguments': {
                            # The text output takes a string 'data' constructor
                            # argument
                            'text': "workload two dummy output one"
                        }
                    },
                    'client1': {
                        'type': 'client',
                        'plugin_id': 'dummy'
                    }
                }
            }
        }
    }
}

""" TESTS """


class ConfigTemplating(unittest.TestCase):

    def _dummy_environment(self) -> Environment:
        """ Create an environment object, add the common config source data """
        if not 'dummy' in environment_names():
            environment = new_environment(
                name='dummy', additional_metta_bootstraps=['metta_dummy'])
            environment.config.add_source(
                PLUGIN_ID_SOURCE_DICT).set_data(CONFIG_DATA)

            # this looks magical, but it works because we have structured the
            # fixtures DICT to match default values
            environment.add_fixtures_from_config()

        return get_environment(name='dummy')

    def _dummy_provisioner(self) -> Fixtures:
        """ Return a Fixtures of all WORKLOAD plugins """
        environment = self._dummy_environment()
        return environment.fixtures.get_plugin(type=Type.PROVISIONER)

    def _dummy_workloads(self) -> Fixtures:
        """ Return a Fixtures of all WORKLOAD plugins """
        environment = self._dummy_environment()
        return environment.fixtures.get_filtered(type=Type.WORKLOAD)

    """ Tests """

    def test_dummy_config_basics(self):
        """ some sanity testing on the shared config object """
        environment = self._dummy_environment()

        dummy_config = environment.config.load('fixtures')
        self.assertEqual(dummy_config.get('prov1.plugin_id'), "dummy")

        dummy_config.get('work1', validator="jsonschema:plugin")

    def test_provisioner_sanity(self):
        """ some sanity testing on loading a provisioner """
        provisioner = self._dummy_provisioner()
        self.assertIsInstance(provisioner, DummyProvisionerPlugin)

    def test_workloads_sanity(self):
        """ test that we can load the workloads """
        workloads = self._dummy_workloads()

        workload_one = workloads.get_plugin(instance_id='work1')
        self.assertIsInstance(workload_one, DummyWorkloadPlugin)

        with self.assertRaises(KeyError):
            workloads['does.not.exist']

    def test_provisioner_workflow(self):
        """ test that the provisioner can follow a decent workflow """
        provisioner = self._dummy_provisioner()

        provisioner.prepare()
        provisioner.apply()

        # ...

        provisioner.destroy()

    def test_workloads_outputs(self):
        """ test that the dummy workload got its outputs from configuration """
        workloads = self._dummy_workloads()
        workload_two = workloads.get_plugin(instance_id='work2')

        self.assertEqual(workload_two.get_output(
            instance_id='output1').get_output(), "workload two dummy output one")

    def test_provisioner_outputs(self):
        """ test that the provisioner produces the needed clients """
        provisioner = self._dummy_provisioner()
        provisioner.prepare()

        # check that we can get an output from a provisioner
        provisioner_output_dummy = provisioner.get_output(
            instance_id='output1')
        self.assertEqual(
            provisioner_output_dummy.get_output(),
            "prov dummy output one")

        # make sure that an error is raised if the key doesn't exist
        with self.assertRaises(KeyError):
            provisioner.get_output(instance_id='does not exist')

    def test_provisioner_clients(self):
        """ test that the provisioner produces the needed clients """
        provisioner = self._dummy_provisioner()
        provisioner.prepare()

        # two ways to get the same client in this case
        client_one = provisioner.get_client(instance_id='client1')
        self.assertIsInstance(client_one, DummyClientPlugin)
        self.assertEqual(client_one.instance_id, 'client1')
        client_dummy = provisioner.get_client(plugin_id='dummy')
        self.assertIsInstance(client_dummy, DummyClientPlugin)
        self.assertEqual(client_dummy.instance_id, 'client1')

        # make sure that an error is raised if the key doesn't exist
        with self.assertRaises(KeyError):
            provisioner.get_client(plugin_id='does not exist')

    def test_clients(self):
        """ test that the provisioner clients behave like clients """
        provisioner = self._dummy_provisioner()
        provisioner.prepare()

        client_one = provisioner.get_client(instance_id='client1')
        self.assertIsInstance(client_one, DummyClientPlugin)

        # test that the dummy plugin can load a text output
        client_one_output = client_one.get_output(instance_id='output1')
        self.assertEqual(
            client_one_output.get_output(),
            "prov client one output one")

        # test that the dummy plugin can load a dict output
        client_two_output = client_one.get_output(instance_id='output2')
        # Test dict as a loaded config plugin
        self.assertEqual(
            client_two_output.get_output('1.1'),
            "prov client one output two data one.one")
