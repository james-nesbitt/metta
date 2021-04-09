"""

Test the binhelper utility plugin

"""
import unittest
import tempfile
import os
import shutil
import logging

from configerus.contrib.dict import PLUGIN_ID_SOURCE_DICT

from mirantis.testing.metta import new_environment, environment_names, get_environment
from mirantis.testing.metta.environment import Environment

logger = logging.getLogger('test-binhelper')


CONFIG_DATA = {
    'fixtures': {
        'bin-helper': {
            'type': 'metta.plugins.utility',
            'plugin_id': 'bin-helper',

            'from_config': True,

            'path': {
                'local': "THIS WILL GET SET IN setUpClass",
                'add_to_path': True,
            },
            'platforms': {
                'Linux-x86_64': {
                    'kubectl': {
                        'url': 'https://dl.k8s.io/release/v1.20.4/bin/linux/amd64/kubectl',
                        'version': 'v1.20.4',
                    },
                    'launchpad': {
                        'url': 'https://github.com/Mirantis/launchpad/releases/download/1.2.0-rc.1/launchpad-linux-x64',
                        'version': '1.2.0-rc.1',
                        'copy': {
                            'launchpad': 'launchpad-linux-x64'
                        }
                    },
                    'helm': {
                        'url': 'https://get.helm.sh/helm-v3.5.3-linux-amd64.tar.gz',
                        'version': 'v3.5.3',
                        'copy': {
                            'helm': 'linux-amd64/helm'
                        }
                    },
                    'terraform': {
                        'url': 'https://releases.hashicorp.com/terraform/0.14.7/terraform_0.14.7_linux_amd64.zip',
                        'version': '0.14.7',
                        'copy': {
                            'terraform': 'terraform'
                        }
                    },
                    'sonobuoy': {
                        'url': 'https://github.com/vmware-tanzu/sonobuoy/releases/download/v0.50.0/sonobuoy_0.50.0_linux_amd64.tar.gz',
                        'version': 'v0.50.0',
                        'copy': {
                            'sonobuoy': 'sonobuoy'
                        }
                    }
                }
            }
        }
    }
}
""" Config data used to create a binhelper fixture

We will use a tempdir for the local path, which will be assigned in the
constructor so that we can manage the context.

"""


""" TESTS """


class BinHelperTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """
            We do 2 important things here:

            1. empty out the ENV of a PATH variable so that binhelper doesn't
               detect any bins in the test system
            2. load the test config but overwrite the local path with a tempdir
               for proper testing.  We will rmtree the tempdir in the desctructor

        """
        os.environ['PATH'] = ''
        cls.temp_bin_dir = tempfile.mkdtemp(prefix='metta_test_')
        cls.config = CONFIG_DATA
        cls.config['fixtures']['bin-helper']['path']['local'] = cls.temp_bin_dir

    @classmethod
    def tearDownClass(cls):
        """ delete the temp dir created in the constructor """
        shutil.rmtree(cls.temp_bin_dir)

    def _environment(self) -> Environment:
        """ Create an environment object, add the common config source data """
        if not 'default' in environment_names():

            environment = new_environment(name='default')
            environment.config.add_source(
                PLUGIN_ID_SOURCE_DICT).set_data(self.config)

            # this looks magical, but it works because we have structured the
            # fixtures DICT to match default values
            environment.add_fixtures_from_config()

        return get_environment(name='default')

    """ Tests """

    def test_config_basics(self):
        """ some sanity testing on the shared config object """
        logger.warning(
            "Creating environment object, which will try to download all of the bins")
        environment = self._environment()

        fixtures_config = environment.config.load('fixtures')
        self.assertEqual(fixtures_config.get(
            'bin-helper.plugin_id'), "bin-helper")
        self.assertEqual(
            fixtures_config.get('bin-helper.path.local'),
            self.temp_bin_dir)

        self.assertTrue(self.temp_bin_dir in os.environ['PATH'])

        self.assertEqual(len(fixtures_config.get(
            'bin-helper.platforms').keys()), 1)
        self.assertEqual(len(fixtures_config.get(
            'bin-helper.platforms.Linux-x86_64').keys()), 5)

        print('Path: {}'.format(self.temp_bin_dir))

    def test_predefined_bins(self):
        """ test that the binhelper automatically loaded a bin from config """

        self.assertIsNotNone(shutil.which('kubectl'))
        self.assertIsNotNone(shutil.which('launchpad'))
        self.assertIsNotNone(shutil.which('terraform'))
        self.assertIsNotNone(shutil.which('helm'))
        self.assertIsNotNone(shutil.which('sonobuoy'))

        list_dir = os.listdir(self.temp_bin_dir)
        self.assertTrue('kubectl' in list_dir)
        self.assertTrue('launchpad' in list_dir)
        self.assertTrue('terraform' in list_dir)
        self.assertTrue('helm' in list_dir)
        self.assertTrue('sonobuoy' in list_dir)
