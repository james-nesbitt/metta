"""

Launchpad MTT provisioner pluging

"""

import json
import yaml
import os.path
import subprocess
import logging
from typing import List

import uctt
from uctt.instances import PluginInstances
from uctt.provisioner import ProvisionerBase
from uctt.client import UCTT_PLUGIN_TYPE_CLIENT
from uctt.contrib.common import UCTT_PLUGIN_ID_OUTPUT_DICT
from uctt.contrib.docker import UCTT_PLUGIN_ID_DOCKER_CLIENT
from uctt.contrib.kubernetes import UCTT_PLUGIN_ID_KUBERNETES_CLIENT


import mirantis.testing.mtt as mtt

logger = logging.getLogger('mirantis.testing.mtt.provisioner:launchpad')

MTT_LAUNCHPAD_CONFIG_LABEL = 'launchpad'
""" Launchpad config label for configuration """
MTT_LAUNCHPAD_CONFIG_BACKEND_KEY = 'backend'
""" Launchpad config backend key """
MTT_LAUNCHPAD_CLI_CONFIG_FILE_KEY = 'config_file'
""" Launchpad config cli key to tell us where to put the launchpad yml file """
MTT_LAUNCHPAD_CLI_WORKING_DIR_KEY = 'working_dir'
""" Launchpad config cli configuration working dir key """
MTT_LAUNCHPAD_CONFIG_BACKEND_LAUNCHPADFILE_OUTPUT_KEY = 'backend.launchpad_output'
""" which config key will tell me the id of the backend output that will give me launchpad yml """
MTT_LAUNCHPAD_BACKEND_OUTPUT_INSTANCE_ID_DEFAULT = 'mke_cluster'
""" Launchpad backend default output name for configuring launchpad """
MTT_LAUNCHPAD_CLI_CONFIG_FILE_DEFAULT = './launchpad.yml'
""" Launchpad config configuration file key """


class LaunchpadProvisionerPlugin(ProvisionerBase):
    """ Launchpad provisioner class

    Provision a system using Mirantis launchpad

    Launchpad is a parasitic priovisioner as it does not create any infra
    but rather it installs into an existing cluster created by a backend plugin.

    If your system is running before you run your test system then use the
    mtt_common.plugins.provisioner.ExistingProvisionerPlugin options and include
    the launchpad config (yaml) in that provisioner configuration

    """

    def prepare(self):
        """ Prepare the provisioning cluster for install

        Primarily here we focus on interpreting the configuration and creating
        the backend plugin.
        We do run the backend.prepare() as well

        """

        """ Set an empty client, populated after the backend is provisioned """
        self.client = None
        """ A configured LaunchpadClient """

        self.downloaded_bundle_users = []
        """ track user bundles that have been downloaded to avoid unecessary repeats """

        """ load all of the launchpad configuration """
        launchpad_config = self.config.load(MTT_LAUNCHPAD_CONFIG_LABEL)

        self.working_dir = launchpad_config.get(
            MTT_LAUNCHPAD_CLI_WORKING_DIR_KEY)
        """ if launchpad needs to be run in a certain path, set it with this config """
        if not self.working_dir:
            self.working_dir = MTT_LAUNCHPADCLIENT_WORKING_DIR_DEFAULT

        """ Configure the backend plugin """

        # here we try to create a provisioner plugin to act as the launchpad plugin.
        # We rely on the launchpad .get('backend') configuration to look like a provisioner
        # and also provide us with an output name
        # We load the backend provisioenr as we would any provisioner, but pointing to
        # our backend config.
        self.backend_output_instance_id = '{}-backend'.format(self.instance_id)
        self.backend = uctt.new_provisioner_from_config(
            config=self.config,
            label=MTT_LAUNCHPAD_CONFIG_LABEL,
            base=MTT_LAUNCHPAD_CONFIG_BACKEND_KEY,
            instance_id=self.backend_output_instance_id)

        self.backend_output_name = launchpad_config.get(
            MTT_LAUNCHPAD_CONFIG_BACKEND_LAUNCHPADFILE_OUTPUT_KEY, exception_if_missing=False)
        """ Backend provisioner give us this output as a source of launchpad yaml """

        # yes, it happenned once, and it creates an infinite loop
        if self.backend.instance_id == self.instance_id:
            raise Exception(
                "It looks like the launchpad provisioner has itself registered as its own backend. This will create an infinite loop.")

        # decide on a path for the runtime launchpad.yml file
        self.config_file = launchpad_config.get(
            MTT_LAUNCHPAD_CLI_CONFIG_FILE_KEY,
            exception_if_missing=False)
        if not self.config_file:
            self.config_file = os.path.realpath(
                MTT_LAUNCHPAD_CLI_CONFIG_FILE_DEFAULT)

        """ prepare the provisioner to be brought up """
        self.backend.prepare(
            label=MTT_LAUNCHPAD_CONFIG_LABEL,
            base=MTT_LAUNCHPAD_CONFIG_BACKEND_KEY)

    def apply(self):
        """ bring a cluster up

        First use the backend to bring up any needed resources, then pull the backend
        output that is expected to contain the launchpad yml, then use that yaml
        to create a LaunchpadClient instance, and use that to install the cluster.

        Raises:
        -------

        ValueError if the object has been configured (prepare) with config that
            doesn't work, or if the backend doesn't give valid yml

        Exception if launchpad fails.

        """

        logger.info(
            "Launchpad provisioner bringing up cluster using %s backend plugin",
            self.backend_output_instance_id)
        self.backend.apply()

        # Get the backend output that holds laucnhpad yaml
        try:
            output = self.backend.get_output(
                instance_id=self.backend_output_name)
        except KeyError as e:
            raise Exception(
                "Launchpad could not retrieve YML configuration from the backend [{}] : ".format(self.backend_output_name, e)) from e
        if not output:
            raise ValueError(
                "Launchpad did not get necessary config from the backend output '%s'",
                self.backend_output_name)
        os.makedirs(
            os.path.dirname(
                os.path.realpath(
                    self.config_file)),
            exist_ok=True)
        with open(os.path.realpath(self.config_file), 'w') as file:
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

            file.write(output if output else '')

        logger.debug("Creating Launchpad API client")
        self.client = LaunchpadClient(
            config_file=self.config_file,
            working_dir=self.working_dir)
        try:
            logger.info(
                "Using launchpad to install products onto backend cluster")
            self.client.install()
        except Exception as e:
            raise Exception("Launchpad failed to install") from e

    def destroy(self):
        """ Tell the backend to bring down any created resources """
        if not self.backend:
            logger.warn("Asked to destroy() but we didn't make a backend yet")

        logger.info(
            "Launchpad provisioner bringing up cluster using %s backend plugin",
            self.backend.instance_id)
        self.backend.destroy()
        self.output = None

    """ CLUSTER INTERACTION """

    def get_output(self, name: str):
        """ Get the outputs, either the launchpad yml or a backend output """
        pass

    def get_clients(self, user: str = 'admin',
                    reload: bool = False) -> PluginInstances:
        """ Get all of the clients """

        bundle_info = self._mke_client_bundle(user, reload)
        """ holds retrieved bundle information from MKE """

        instances = PluginInstances(self.config)

        kube_config = os.path.join(bundle_info['path'], 'kube.yml')
        if not os.path.exists(kube_config):
            raise NotImplemented(
                "Launchpad was asked for a kubernetes client, but not kube config file was in the client bundle.  Are you sure this is a kube cluster?")

        instance_id = "launchpad-{}-{}-client".format(
            self.instance_id, UCTT_PLUGIN_ID_KUBERNETES_CLIENT)
        plugin = instances.add_plugin(
            type=UCTT_PLUGIN_TYPE_CLIENT,
            plugin_id=UCTT_PLUGIN_ID_KUBERNETES_CLIENT,
            instance_id=instance_id,
            priority=80)
        plugin.arguments(kube_config_file=kube_config)

        try:
            host = bundle_info['Endpoints']['docker']['Host']
            cert_path = bundle_info['tls_paths']['docker']
        except TypeError as e:
            logger.error(
                "Could not read client bundle properly: %s",
                bundle_info['Endpoints']['docker']['Host'])
            raise e

        instance_id = "launchpad-{}-{}-client".format(
            self.instance_id, UCTT_PLUGIN_ID_DOCKER_CLIENT)
        plugin = instances.add_plugin(
            type=UCTT_PLUGIN_TYPE_CLIENT,
            plugin_id=UCTT_PLUGIN_ID_DOCKER_CLIENT,
            instance_id=instance_id,
            priority=80)
        plugin.arguments(host=host, cert_path=cert_path)

        return instances

    def get_client(self, plugin_id: str = '', instance_id: str = '',
                   exception_if_missing: bool = True, user='admin'):
        """ Make a client for interacting with the cluster """

        instances = self.get_clients(user)
        plugin = instances.get_plugin(
            type=UCTT_PLUGIN_TYPE_CLIENT,
            plugin_id=plugin_id,
            instance_id=instance_id,
            exception_if_missing=exception_if_missing)
        return plugin

    def _mke_client_bundle(self, user: str, reload: bool = False):
        """ Retrieve the MKE Client bundle metadata using the client """

        assert self.client, "Don't have a launchpad client configured yet"
        return self.client.bundle(user, reload)


MTT_LAUNCHPADCLIENT_WORKING_DIR_DEFAULT = '.'
""" Launchpad Client default working dir """
MTT_LAUNCHPADCLIENT_BIN_PATH = 'launchpad'
""" Launchpad bin exec for the subprocess """

MTT_USER_LAUNCHPAD_CLUSTER_PATH = os.path.expanduser(
    os.path.join('~', '.mirantis-launchpad', 'cluster'))
""" the str path to where launchpad keeps its user config """
MTT_USER_LAUNCHPAD_BUNDLE_SUBPATH = 'bundle'
""" str path to user bundle config can be found when it is downloaded """
MTT_USER_LAUNCHPAD_BUNDLE_META_FILE = 'meta.json'
""" str filename for the meta file in the client bundle path """


class LaunchpadClient:
    """ shell client for interacting with the launchpad bin """

    def __init__(self, config_file: str = MTT_LAUNCHPAD_CLI_CONFIG_FILE_DEFAULT,
                 working_dir: str = MTT_LAUNCHPADCLIENT_WORKING_DIR_DEFAULT):
        """
        Parameters:

        config_file (str) : path to launchpad config file, typically
            launchpad.yml

        working_dir (str) : full config file path.
            this typically plays a role in interpreting file paths from the
            config for things like ssh keys.  The client will use that path for
            python subprocess execution

        """
        self.config_file = config_file
        """ Path to config file """
        self.working_dir = working_dir
        """ Python subprocess working dir to execute launchpad in.
            This may be relevant in cases where ssh keys have a relative path """

        self.bin = MTT_LAUNCHPADCLIENT_BIN_PATH
        """ shell execution target for launchpad """

        self.downloaded_bundle_users = []
        """ hold a list of bundles we've downloaded to avoid repeats """

    def install(self):
        """ Install using the launchpad client """
        self._run(['apply'])
        self.downloaded_bundle_users = []

    def bundle(self, user: str, reload: bool = False):
        """ Retrieve a client bundle and return the metadata as a dict """
        client_bundle_path = self._mke_client_bundle_path(user)
        client_bundle_meta_file = os.path.join(
            client_bundle_path, MTT_USER_LAUNCHPAD_BUNDLE_META_FILE)

        if reload or not os.path.isfile(
                client_bundle_meta_file) or not user in self.downloaded_bundle_users:
            self._run(["client-config", user])
            self.downloaded_bundle_users.append(user)

        data = {}
        """ Will hold data pulled from the client meta data file """
        try:
            with open(client_bundle_meta_file) as json_file:
                data = json.load(json_file)
        except FileNotFoundError as e:
            raise ValueError(
                "failed to open the launchpad client bundle meta file.") from e

        # add some stuff that a client bundle always has
        data['path'] = client_bundle_path
        # this stuff should already be in the bundle, but it isn't
        data['tls_paths'] = {
            'docker': os.path.join(client_bundle_path, 'tls', 'docker'),
            'kubernetes': os.path.join(client_bundle_path, 'tls', 'kubernetes'),
        }

        return data

    def _mke_client_bundle_path(self, user: str):
        """ find the path to a client bundle for a user """
        return os.path.join(MTT_USER_LAUNCHPAD_CLUSTER_PATH,
                            self._cluster_name(), MTT_USER_LAUNCHPAD_BUNDLE_SUBPATH, user)

    def _cluster_name(self):
        """ get the cluster name from the config file

        @TODO we should cache it, but then do we need to invalidate cache?

        """
        try:
            with open(self.config_file) as config_file_object:
                self.config_data = yaml.load(
                    config_file_object, Loader=yaml.FullLoader)
                """ keep a parsed copy of the launchpad file """
        except Exception as e:
            raise ValueError(
                ValueError(
                    "Launchpad yaml file had unexpected contents: {}".format(config_file))) from e

        if not isinstance(self.config_data, dict):
            raise ValueError(
                "Launchpad yaml file had unexpected contents: {}".format(config_file))

        return self.config_data['metadata']['name']

    def _run(self, args: List[str] = ['help']):
        """ Run a launchpad command

        Parameters:

        args (List[str]) : arguments to pass to the launchpad bin using
            subprocess

        """

        """ if the command passed uses a config file, add the flag for it """
        if not args[0] in ['help']:
            args = [args[0]] + ['-c', self.config_file] + args[1:]

        cmd = [self.bin] + args

        exec = subprocess.run(cmd, cwd=self.working_dir)
        exec.check_returncode()
