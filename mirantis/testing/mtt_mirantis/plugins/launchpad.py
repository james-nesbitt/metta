"""

Launchpad MTT provisioner pluging

"""

import json
import os.path
import subprocess
import logging
from typing import List

import mirantis.testing.mtt as mtt
from mirantis.testing.mtt.client import make_client
from mirantis.testing.mtt.provisioner import ProvisionerBase
import mirantis.testing.mtt_common as mtt_common
import mirantis.testing.mtt_docker as mtt_docker
import mirantis.testing.mtt_kubernetes as mtt_kubernetes

logger = logging.getLogger("mirantis.testing.mtt_mirantis:launchpad_prov")

MTT_LAUNCHPAD_CONFIG_LABEL = 'launchpad'
""" Launchpad config label for configuration """
MTT_LAUNCHPAD_CONFIG_BACKEND_CLUSTER_NAME_KEY = 'cluster_name'
""" Launchpad config backend cluster_name key """
MTT_LAUNCHPAD_CONFIG_BACKEND_PLUGIN_ID_KEY = 'backend.plugin_id'
""" Launchpad config backend plugin_id key """
MTT_LAUNCHPAD_CONFIG_BACKEND_OUTPUT_KEY = 'backend.output'
""" Launchpad config backend plugin_id key """
MTT_LAUNCHPAD_CONFIG_BACKEND_CONFIG_KEY = 'backend.config'
""" Launchpad config backend config overrides """
MTT_LAUNCHPAD_CLI_CONFIG_FILE_KEY = 'config_file'
""" Launchpad config cli configuration file key """

MTT_LAUNCHPAD_BACKEND_OUTPUT_NAME_DEFAULT = 'mke_cluster'
""" Launchpad backend default output name for configuring launchpad """
MTT_LAUNCHPAD_CLI_CONFIG_FILE_DEFAULT = './launchpad.yml'
""" Launchpad config configuration file key """

MTT_USER_LAUNCHPAD_CLUSTER_PATH = os.path.join(os.path.expanduser('~'), '.mirantis-launchpad', 'cluster')
""" the str path to where launchpad keeps its user config """
MTT_USER_LAUNCHPAD_BUNDLE_SUBPATH = 'bundle'
""" str path to user bundle config can be found when it is downloaded """
MTT_USER_LAUNCHPAD_BUNDLE_META_FILE = 'meta.json'
""" str filename for the meta file in the client bundle path """

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

        self.cluster_name = launchpad_config.get(MTT_LAUNCHPAD_CONFIG_BACKEND_CLUSTER_NAME_KEY)

        self.backend_plugin_id = launchpad_config.get(
            MTT_LAUNCHPAD_CONFIG_BACKEND_PLUGIN_ID_KEY,
            exception_if_missing=True)
        self.backend_output_name = launchpad_config.get(
            MTT_LAUNCHPAD_CONFIG_BACKEND_OUTPUT_KEY,
            exception_if_missing=False)
        if not self.backend_output_name:
            self.backend_output_name = MTT_LAUNCHPAD_BACKEND_OUTPUT_NAME_DEFAULT

        self.config_file = launchpad_config.get(
            MTT_LAUNCHPAD_CLI_CONFIG_FILE_KEY,
            exception_if_missing=False)
        if not self.config_file:
            self.config_file =  os.path.realpath(MTT_LAUNCHPAD_CLI_CONFIG_FILE_DEFAULT)

        logger.info("Launchpad provisioner now attempting to load %s backend plugin", self.backend_plugin_id)
        backend_provisioner_instance_id = "{}_backend".format(self.instance_id)
        backend_provisioner_config_label = "{}_launchpad_backend_provisioner".format(self.instance_id)

        backend_provisioner_config_data = launchpad_config.get(MTT_LAUNCHPAD_CONFIG_BACKEND_CONFIG_KEY)
        if not backend_provisioner_config_data:
            backend_provisioner_config_data = {
                backend_provisioner_config_label: {
                    mtt.MTT_PROVISIONER_CONFIG_KEY_PLUGINID: self.backend_plugin_id
                }
            }

        backend_provisioner_config_priority = self.config.default_priority()+10
        self.config.add_source(mtt_common.MTT_PLUGIN_ID_CONFIGSOURCE_DICT, backend_provisioner_instance_id, backend_provisioner_config_priority).set_data(backend_provisioner_config_data)
        self.backend = mtt.new_provisioner_from_config(self.config, backend_provisioner_instance_id, backend_provisioner_config_label)

        if self.backend.instance_id == self.instance_id:
            raise Exception("It looks like the launchpad provisioner has itself registered as its own backend. This will create an infinite loop.")

        """ prepare the provisioner to be brought up """
        self.backend.prepare()

    def apply(self):
        """ pretend to bring a cluster up """

        logger.info("Launchpad provisioner bringing up cluster using %s backend plugin", self.backend_plugin_id)
        self.backend.apply()

        # @TODO make something less terraform specific to get the launchpad yml file
        try:
            output = self.backend.output(self.backend_output_name)
        except Exception as e:
            raise Exception("Launchpad could not retrieve YML configuration from the backend") from e
        if not output:
            raise ValueError("Launchpad did not get necessary config from the backend output '%s'", self.backend_output_name)
        os.makedirs(os.path.dirname(os.path.realpath(self.config_file)), exist_ok=True)
        with open(os.path.realpath(self.config_file), 'w') as file:
            file.write(output if output else "")

        self.client = LaunchpadClient(config_file=self.config_file, working_dir=self.backend.working_dir)
        logger.info("Using launchpad to install products onto backend cluster")
        try:
            self.client.install()
            # forget about any bundles we downloaded as they may be invalid now
            self.downloaded_bundle_users = []
            pass
        except Exception as e:
            raise Exception("Launchpad failed to install") from e

    def destroy(self):
        """ pretend to brind a cluster down """
        logger.info("Launchpad provisioner bringing up cluster using %s backend plugin", self.backend_plugin_id)
        self.backend.destroy()
        self.output = None

    """ CLUSTER INTERACTION """

    def info(self):
        """ Get some readable info about the test cluster """
        info = {
            "provisioner": __file__,
            "backend": self.backend_plugin_name,
            "output": self.output
        }
        return info

    def get_client(self, type:str, user:str='admin'):
        """ Make a client for interacting with the cluster """

        bundle_info = self._mke_client_bundle(user)
        client_bundle_path = self._mke_client_bundle_path(user)

        # @TODO get this into a public enum
        if type == mtt_kubernetes.MTT_PLUGIN_ID_KUBERNETES_CLIENT:
            kube_config = os.path.join(client_bundle_path, "kube.yml")
            if not os.path.exists(kube_config):
                raise NotImplemented("Launchpad was asked for a kubernetes client, but not kube config file was in the client bundle.  Are you sure this is a kube cluster?")

            instance_id = "launchpad-{}-kubernetes-client".format(self.instance_id)
            kubernetes_client = make_client(mtt_kubernetes.MTT_PLUGIN_ID_KUBERNETES_CLIENT, self.config, instance_id)
            kubernetes_client.args(kube_config)
            return kubernetes_client

        # Asked for a docker client
        elif type == mtt_docker.MTT_PLUGIN_ID_DOCKER_CLIENT:
            try:
                host = bundle_info["Endpoints"]["docker"]["Host"]
                cert_path = bundle_info["tls_paths"]["docker"]
            except TypeError as e:
                logger.error("Could not read client bundle properly: %s", bundle_info["Endpoints"]["docker"]["Host"])
                raise e

            instance_id = "launchpad-{}-docker-client".format(self.instance_id)
            docker_client = make_client(mtt_docker.MTT_PLUGIN_ID_DOCKER_CLIENT, self.config, instance_id)
            docker_client.args(host, cert_path)
            return docker_client

        else:
            raise KeyError("Launchpad cannot create client, unknown type %s", type)

    def _exec(self, target: str, cmd: List[str]):
        """ Execute a command on some of the hosts

        A complicated operation for logistics.

        Returns:

        Dict[str,str] of responses for each node on which it was executed keyed
        to the HOSTNAME of the node
        """
        pass

    def _mke_client_bundle_path(self, user:str):
        """ find teh path to a client bundle for a user """
        return os.path.join(MTT_USER_LAUNCHPAD_CLUSTER_PATH, self.cluster_name,  MTT_USER_LAUNCHPAD_BUNDLE_SUBPATH, user)

    def _mke_client_bundle(self, user: str, reload: bool=False):
        """ Retrieve the MKE Client bundle """

        assert self.client, "Don't have a launchpad client configured yet"

        client_bundle_path = self._mke_client_bundle_path(user)
        client_bundle_meta_file = os.path.join(client_bundle_path, MTT_USER_LAUNCHPAD_BUNDLE_META_FILE)

        if reload or not user in self.downloaded_bundle_users:
            self.client.bundle(user)
            # doubles in the array are not a big deal
            self.downloaded_bundle_users.append(user)

        with open(client_bundle_meta_file) as json_file:
            data = json.load(json_file)

        data['path'] = client_bundle_path
        data['tls_paths'] = {
            "docker": os.path.join(client_bundle_path, "tls", "docker"),
            "kubernetes": os.path.join(client_bundle_path, "tls", "kubernetes"),
        }

        return data

MTT_LAUNCHPADCLIENT_CONFIGFILE_DEFAULT = './launchpad.yml'
""" Launchpad Client default config file """
MTT_LAUNCHPADCLIENT_WORKING_DIR_DEFAULT = '.'
""" Launchpad Client default working dir """
MTT_LAUNCHPADCLIENT_BIN_PATH = 'launchpad'
""" Launchpad bin exec for the subprocess """

class LaunchpadClient:
    """ shell client for interacting with the launchpad bin """

    def __init__(self, config_file:str=MTT_LAUNCHPADCLIENT_CONFIGFILE_DEFAULT,
                 working_dir:str=MTT_LAUNCHPADCLIENT_WORKING_DIR_DEFAULT):
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

        self.bin = MTT_LAUNCHPADCLIENT_BIN_PATH
        """ shell execution target for launchpad """

    def install(self):
        self.exec(["apply"])

    def upgrade(self):
        """ Upgrade the cluster """
        pass

    def bundle(self, user:str):
        """ Upgrade the cluster """
        self.exec(["client-config", user])

    def exec(self, args:List[str]=['help']):
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
