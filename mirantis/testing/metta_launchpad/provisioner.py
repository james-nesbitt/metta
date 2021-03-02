"""

Launchpad metta provisioner pluging


Launchpad is a parasitic priovisioner as it does not create any infra
but rather it installs into an existing cluster defined by an output.

If your system is running before you run your test system then use the
metta.contrib.dummy.provisioner provisioner and include the launchpad
config (yaml) in that provisioner configuration as an output. Otherwise
use a provisioner such as the terraform provisioner before this one.

"""

import json
import yaml
import os.path
import logging
from typing import List, Dict, Any

from configerus.loaded import LOADED_KEY_ROOT
from configerus.contrib.jsonschema.validate import PLUGIN_ID_VALIDATE_JSONSCHEMA_SCHEMA_CONFIG_LABEL
from configerus.validator import ValidationError

from mirantis.testing.metta.plugin import METTAPlugin, Type
from mirantis.testing.metta.fixtures import Fixtures, UCCTFixturesPlugin
from mirantis.testing.metta.provisioner import ProvisionerBase
from mirantis.testing.metta_docker import METTA_PLUGIN_ID_DOCKER_CLIENT
from mirantis.testing.metta_kubernetes import METTA_PLUGIN_ID_KUBERNETES_CLIENT

from .launchpad import LaunchpadClient, METTA_USER_LAUNCHPAD_CLUSTER_PATH
from .exec_client import METTA_LAUNCHPAD_EXEC_CLIENT_PLUGIN_ID

logger = logging.getLogger('mirantis.testing.metta.provisioner:launchpad')

METTA_LAUNCHPAD_CONFIG_LABEL = 'launchpad'
""" Launchpad config label for configuration """
METTA_LAUNCHPAD_CONFIG_ROOT_PATH_KEY = 'root.path'
""" config key for a base path that should be used for any relative paths """
METTA_LAUNCHPAD_CLI_CONFIG_FILE_KEY = 'config_file'
""" Launchpad config cli key to tell us where to put the launchpad yml file """
METTA_LAUNCHPAD_CLI_WORKING_DIR_KEY = 'working_dir'
""" Launchpad config cli configuration working dir key """
METTA_LAUNCHPAD_CLI_WORKING_CLUSTEROVERRIDE = 'cluster_name'
""" If provided, this config key will override a cluster name pulled from yaml"""
METTA_LAUNCHPAD_CONFIG_OUTPUTSOURCE_LAUNCHPADFILE_OUTPUT_KEY = 'source_output.instance_id'
""" which config key will tell me the id of the backend output that will give me launchpad yml """
METTA_LAUNCHPAD_CLI_CONFIG_DOCKER_VERSION_DEFAULT = '1.40'
""" Default value for the docker client version number.  It would be best to discover or config this."""
METTA_LAUNCHPAD_BACKEND_OUTPUT_INSTANCE_ID_DEFAULT = 'mke_cluster'
""" Launchpad backend default output name for configuring launchpad """
METTA_LAUNCHPAD_CLI_CONFIG_ISINSTALLED = 'is_installed'
""" Boolean config value that tells the provisioner to try to load clients before running apply """

METTA_LAUNCHPAD_VALIDATE_JSONSCHEMA = {
    'type': 'object',
    'properties': {
        'type': {'type': 'string'},
        'plugin_id': {'type': 'string'},

        'root': {
            'type': 'object',
            'properties': {
                'path': {'type': 'string'}
            }
        },
        'source_output': {
            'type': 'object',
            'properties': {
                'instance_id': {'type': 'string'}
            },
            'required': ['instance_id']
        },
        'cluster_name': {
            'type': 'string'
        },
        'config_file': {
            'type': 'string'
        },
        'working_dir': {
            'type': 'string'
        }
    },
    'required': ['source_output']
}
""" Validation jsonschema for terraform config contents """
METTA_LAUNCHPAD_VALIDATE_TARGET = "{}:{}".format(
    PLUGIN_ID_VALIDATE_JSONSCHEMA_SCHEMA_CONFIG_LABEL,
    METTA_LAUNCHPAD_CONFIG_LABEL)
""" configerus validation target to matche the above config, which relates to the bootstrap in __init__.py """


class LaunchpadProvisionerPlugin(ProvisionerBase, UCCTFixturesPlugin):
    """ Launchpad provisioner class

    Provision a system using Mirantis launchpad

    """

    def __init__(self, environment, instance_id,
                 label: str = METTA_LAUNCHPAD_CONFIG_LABEL, base: Any = LOADED_KEY_ROOT):
        """ Run the super constructor but also set class properties """
        ProvisionerBase.__init__(self, environment, instance_id)
        UCCTFixturesPlugin.__init__(self)

        """ Set an empty client, populated after the backend is provisioned """
        self.client = None
        """ A configured LaunchpadClient """

        self.downloaded_bundle_users = []
        """ track user bundles that have been downloaded to avoid unecessary repeats """

        self.config_label = label
        self.config_base = base

        """ load all of the launchpad configuration """
        launchpad_config = self.environment.config.load(label)

        # Run confgerus validation on the config using our above defined
        # jsonschema
        try:
            launchpad_config.get(
                base, validator=METTA_LAUNCHPAD_VALIDATE_TARGET)
        except ValidationError as e:
            raise ValueError(
                "Launchpad config failed validation: {}".format(e)) from e

        self.working_dir = launchpad_config.get(
            [base, METTA_LAUNCHPAD_CLI_WORKING_DIR_KEY])
        """ if launchpad needs to be run in a certain path, set it with this config """
        if not self.working_dir:
            self.working_dir = METTA_LAUNCHPADCLIENT_WORKING_DIR_DEFAULT
        if not os.path.isabs(self.working_dir):
            # did a relative path root get passed in as config?
            root_path = self.backend_output_name = launchpad_config.get(
                [base, METTA_LAUNCHPAD_CONFIG_ROOT_PATH_KEY])
            if root_path:
                self.working_dir = os.path.join(root_path, self.working_dir)
            self.working_dir = os.path.abspath(self.working_dir)

        """ Retrieve the configuration for the output plugin """
        try:
            self.backend_output_name = launchpad_config.get(
                [base, METTA_LAUNCHPAD_CONFIG_OUTPUTSOURCE_LAUNCHPADFILE_OUTPUT_KEY], exception_if_missing=True)
            """ Backend provisioner give us this output as a source of launchpad yaml """
        except KeyError as e:
            raise ValueError(
                "Could not find launchpad configuration for backend provisioner output instance_id to get launchpad yml from.")

        # decide on a path for the runtime launchpad.yml file
        self.config_file = launchpad_config.get(
            [base, METTA_LAUNCHPAD_CLI_CONFIG_FILE_KEY], exception_if_missing=False)
        if not self.config_file:
            self.config_file = METTA_LAUNCHPAD_CLI_CONFIG_FILE_DEFAULT
        if not os.path.isabs(self.config_file):
            # A relative [ath for the config file is expected to be relative to
            # the working dir]
            self.config_file = os.path.abspath(
                os.path.join(self.working_dir, self.config_file))

        cluster_name_override = launchpad_config.get(
            [base, METTA_LAUNCHPAD_CLI_WORKING_CLUSTEROVERRIDE], exception_if_missing=False)
        """ Can hardcode the cluster name if it can't be take from the yaml file """

        logger.debug("Creating Launchpad API client")
        self.client = LaunchpadClient(
            config_file=self.config_file,
            working_dir=self.working_dir,
            cluster_name_override=cluster_name_override)

        # If we can, it makes sense to build the docker and k8s client fixtures now.
        # This will only be possible in cases where we have an existing config file
        # and we can download a client bundle.
        # We try that here, even though it is verbose and ugly, so that we have
        # the clients available for introspection.
        # We probably shouldn't, but it allows some flexibility.
        if os.path.exists(self.config_file):
            try:
                self._make_fixtures()
            except BaseException:
                logger.debug(
                    "Launchpad couldn't initialize some plugins as we don't have enough information to go on.")
                # we most likely failed because we don't have enough info get
                # make fixtures from

    def info(self, deep: bool = False):
        """ get info about a provisioner plugin """
        plugin = self
        client = self.client

        info = {
            'plugin': {
                'config_label': plugin.config_label,
                'config_base': plugin.config_base,
                'downloaded_bundle_users': plugin.downloaded_bundle_users,
                'working_dir': plugin.working_dir,
                'backend_output_name': plugin.backend_output_name
            },
            'client': {
                'cluster_name_override': client.cluster_name_override,
                'config_file': client.config_file,
                'working_dir': client.working_dir,
                'bin': client.bin
            }
        }

        if deep:
            try:
                info['config'] = client.describe_config()
                info['bundles'] = {user: client.bundle(
                    user) for user in client.bundle_users()}
            except Exception:
                pass

            fixtures = {}
            for fixture in self.get_fixtures().to_list():
                fixture_info = {
                    'fixture': {
                        'type': fixture.type.value,
                        'plugin_id': fixture.plugin_id,
                        'instance_id': fixture.instance_id,
                        'priority': fixture.priority,
                    }
                }
                if hasattr(fixture.plugin, 'info'):
                    plugin_info = fixture.plugin.info()
                    if isinstance(plugin_info, dict):
                        fixture_info.update(plugin_info)
                fixtures[fixture.instance_id] = plugin_info
            info['fixtures'] = fixtures

        info['helper'] = {
            'commands': {
                'apply': "{workingpathcd}{bin} apply -c {config_file}".format(workingpathcd=("cd {} && ".format(client.working_dir) if not client.working_dir == '.' else ''), bin=client.bin, config_file=client.config_file),
                'client-config': "{workingpathcd}{bin} client-config -c {config_file} {user}".format(workingpathcd=("cd {} && ".format(client.working_dir) if not client.working_dir == '.' else ''), bin=client.bin, config_file=client.config_file, user='admin')
            }
        }

        return info

    def prepare(self):
        """ Prepare the provisioning cluster for install

        We ignore this.

        """
        logger.info(
            'Running Launchpad Prepare().  Launchpad has no prepare stage.')

    def apply(self):
        """ bring a cluster up

        We assume that the cluster is running and the we can pull the required
        yaml from an output fixture in the environment.

        This plugin needs an output fixture, probably of dict type.  It will
        Pull that structure for the launchpad yaml config file and dump it into
        its config path.
        The provisioner can find an output directly from the environment, or
        from a specific fixture source.  If you want the output to come from
        only a specific backend fixture then make sure that a "backend" config
        exists, otherwise just use an "output" config.

        Raises:
        -------

        ValueError if the object has been configured (prepare) with config that
            doesn't work, or if the backend doesn't give valid yml

        Exception if launchpad fails.

        """

        # Get the backend output that holds laucnhpad yaml
        try:
            output = self.environment.fixtures.get_plugin(type=Type.OUTPUT,
                                                          instance_id=self.backend_output_name)
        except KeyError as e:
            raise Exception(
                "Launchpad could not retrieve YML configuration from the backend [{}] : ".format(self.backend_output_name, e)) from e
        if not output:
            raise ValueError(
                "Launchpad did not get necessary config from the backend output '%s'", self.backend_output_name)

        # if our output returns an output plugin (quack) then retrieve the
        # actual output
        if hasattr(output, 'get_output') and callable(
                getattr(output, 'get_output')):
            try:
                output = output.get_output()
            except AttributeError as e:
                raise ValueError(
                    'Backend output for launchpad yaml had not been given any data.  Are you sure that the backend ran?')
        if isinstance(output, dict):
            output = yaml.dump(output)

        # write the launchpad output to our yaml file target (after creating
        # the path)
        os.makedirs(
            os.path.dirname(
                os.path.realpath(
                    self.config_file)),
            exist_ok=True)
        with open(os.path.realpath(self.config_file), 'w') as file:
            file.write(output if output else '')

        try:
            logger.info(
                "Using launchpad to install products onto backend cluster")
            self.client.install()
        except Exception as e:
            raise Exception("Launchpad failed to install") from e

        self._make_fixtures(reload=True)

    def destroy(self):
        """ We don't bother uninstalling at this time

        we do:
        1. delete the generated config file
        2. ask the client to remove any downloaded client bundles

        """
        if os.path.exists(self.config_file):
            os.remove(self.config_file)
        self.client.rm_client_bundles()
        self.client.reset()

    """ CLUSTER INTERACTION """

    def _make_fixtures(self, user: str = 'admin',
                       reload: bool = False) -> Fixtures:
        """ Build fixtures for all of the clients """

        bundle_info = self._mke_client_bundle(user, reload)
        """ holds retrieved bundle information from MKE for all client configs. """

        # KUBE Client

        kube_config = os.path.join(bundle_info['path'], 'kube.yml')
        if not os.path.exists(kube_config):
            raise NotImplemented(
                "Launchpad was asked for a kubernetes client, but not kube config file was in the client bundle.  Are you sure this is a kube cluster?")

        instance_id = "launchpad-{}-{}-{}-client".format(
            self.instance_id, METTA_PLUGIN_ID_KUBERNETES_CLIENT, user)
        fixture = self.environment.add_fixture(
            type=Type.CLIENT,
            plugin_id=METTA_PLUGIN_ID_KUBERNETES_CLIENT,
            instance_id=instance_id,
            priority=70,
            arguments={'kube_config_file': kube_config})
        self.fixtures.add_fixture(fixture)

        # DOCKER CLIENT
        #
        # @NOTE we pass in a docker API constraint because I ran into a case where the
        #   client failed because the python library was ahead in API version

        try:
            host = bundle_info['Endpoints']['docker']['Host']
            cert_path = bundle_info['tls_paths']['docker']
        except TypeError as e:
            logger.error(
                "Could not read client bundle properly: %s",
                bundle_info['Endpoints']['docker']['Host'])
            raise e

        instance_id = "launchpad-{}-{}-{}-client".format(
            self.instance_id, METTA_PLUGIN_ID_DOCKER_CLIENT, user)
        fixture = self.environment.add_fixture(
            type=Type.CLIENT,
            plugin_id=METTA_PLUGIN_ID_DOCKER_CLIENT,
            instance_id=instance_id,
            priority=70,
            arguments={'host': host, 'cert_path': cert_path, 'version': METTA_LAUNCHPAD_CLI_CONFIG_DOCKER_VERSION_DEFAULT})
        self.fixtures.add_fixture(fixture)

        # EXEC CLIENT
        #
        instance_id = "launchpad-{}-{}-{}-client".format(
            self.instance_id, METTA_LAUNCHPAD_EXEC_CLIENT_PLUGIN_ID, user)
        fixture = self.environment.add_fixture(
            type=Type.CLIENT,
            plugin_id=METTA_LAUNCHPAD_EXEC_CLIENT_PLUGIN_ID,
            instance_id=instance_id,
            priority=70,
            arguments={'client': self.client})
        self.fixtures.add_fixture(fixture)

    def _mke_client_bundle(self, user: str, reload: bool = False):
        """ Retrieve the MKE Client bundle metadata using the client """
        assert self.client, "Don't have a launchpad client configured yet"
        return self.client.bundle(user, reload)
