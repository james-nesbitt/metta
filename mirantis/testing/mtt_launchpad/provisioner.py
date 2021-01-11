"""

Launchpad MTT provisioner pluging

"""

import json
import os.path
import subprocess
import logging
import appdirs
from typing import List
from mirantis.testing.toolbox import PluginType, load_plugin
from . import backend_existing

logger = logging.getLogger("mirantis.testing.mtt_launchpad:provisioner")

LAUNCHPAD_BACKEND_EXISTING_PLUGIN_NAME = "existing"
""" If the laucnhpad backend plugin name is this value then we just create a
class instance without a plugin load """

def factory(conf):
    """ Launchpad provisioner plugin factory (see mtt/plugin/factory) """
    return LaunchpadProvisioner(conf)

class LaunchpadProvisioner:
    """ Launchpad provisioner class """

    def __init__(self, conf):
        """ constructor """
        self.conf = conf

        self.launchpad_config = conf.load("launchpad")

        self.backend_plugin_name = self.launchpad_config.get("backend.plugin", exception_if_missing=True)
        self.backend_output_name = self.launchpad_config.get("backend.output", exception_if_missing=False)
        if not self.backend_output_name:
            self.backend_output_name = "mke_cluster"

        """ what launchpad thinks the name of the cluster is """
        self.launchpad_cluster_name = self.launchpad_config.get("cluster_name", exception_if_missing=False)
        if not self.launchpad_cluster_name:
            self.launchpad_cluster_name = "mke_cluster"

        self.config_file = self.launchpad_config.get("config_file", exception_if_missing=False)
        if not self.config_file:
            self.config_file =  os.path.realpath("./launchpad.yml")

        self.user_launchpad_path = os.path.join(os.path.expanduser("~"), ".mirantis-launchpad", "cluster", "launchpad-mke")
        """ the str path to where launchpad keeps its user config """

        self.client_bundle_path = os.path.join(self.user_launchpad_path, "bundle")
        """ Dict of paths for user keys.  "admin" key is the most likely needed """

        self.client = None
        """ A LaunchpadClient configured """

        if self.backend_plugin_name == "existing":
            logger.info("Backend is existing, creating the class directly without plugin load")
            self.backend = backend_existing.ExistingBackendProvisioner(output_name=self.backend_output_name, config_file=self.config_file)
        else:
            logger.info("Launchpad provisioner now attempting to load %s backend plugin", self.backend_plugin_name)
            self.backend = load_plugin(conf, PluginType.PROVISIONER, self.backend_plugin_name)


    def prepare(self):
        """ prepare the provisioner to be brought up """
        self.backend.prepare()

    def up(self):
        """ pretend to bring a cluster up """

        logger.info("Launchpad provisioner bringing up cluster using %s backend plugin", self.backend_plugin_name)
        self.backend.up()

        # @TODO make something less terraform specific to get the launchpad yml file
        output = self.backend.output(self.backend_output_name)
        if not output:
            raise ValueError("Launchpad did not get necessary config from the backend output '%s'", self.backend_output_name)
        os.makedirs(os.path.dirname(os.path.realpath(self.config_file)), exist_ok=True)
        with open(os.path.realpath(self.config_file), 'w') as file:
            file.write(output if output else "")

        self.client = LaunchpadClient(config_file=self.config_file, working_dir=self.backend.working_dir)
        logger.info("Using launchpad to install products onto backend cluster")
        self.client.install()

    def down(self):
        """ pretend to brind a cluster down """
        logger.info("Launchpad provisioner bringing up cluster using %s backend plugin", self.backend_plugin_name)
        self.backend.down()
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

    def get_client(self, type:str):
        """ Make a client for interacting with the cluster """

        bundle_info = self._mke_client_bundle()

        # @TODO get this into a public enum
        if type == "kubernetes":
            client_bundle_path = self._mke_client_bundle_path("admin")
            kube_config = os.path.join(client_bundle_path, "kube.yml")
            return load_plugin(self.conf, PluginType.CLIENT, type, config_file=kube_config)

        elif type == "docker":
            try:
                host = bundle_info["Endpoints"]["docker"]["Host"]
                cert_path = bundle_info["tls_paths"]["docker"]
            except TypeError as e:
                logger.error("Could not read client bundle properly: %s", bundle_info["Endpoints"]["docker"]["Host"])
                raise e

            return load_plugin(self.conf, PluginType.CLIENT, type, host=host, cert_path=cert_path)

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

    def _mke_client_bundle_path(self, user:str = "admin"):
        """ find teh path to a client bundle for a user """
        return os.path.join(self.user_launchpad_path, "bundle", user)

    def _mke_client_bundle(self, user: str="admin", reload: bool=False):
        """ Retrieve the MKE Client bundle """

        assert self.client, "Don't have a launchpad client configured yet"

        client_bundle_path = self._mke_client_bundle_path(user)
        client_bundle_meta_file = os.path.join(client_bundle_path, "meta.json")

        if reload or not os.path.exists(client_bundle_meta_file):
            self.client.bundle(user)


        with open(client_bundle_meta_file) as json_file:
            data = json.load(json_file)

        data['path'] = client_bundle_path
        data['tls_paths'] = {
            "docker": os.path.join(client_bundle_path, "tls", "docker"),
            "kubernetes": os.path.join(client_bundle_path, "tls", "kubernetes"),
        }

        return data

class LaunchpadClient:
    """ shell client for interacting with the launchpad bin """

    def __init__(self, config_file, working_dir: str="."):
        """
        :param: config_file str : path to launchpad config file
        """
        self.config_file = config_file
        """ Path to config file """
        self.working_dir = working_dir

        self.bin = "launchpad"
        """ shell execution target for launchpad """

    def install(self):
        self.exec(["apply"])

    def upgrade(self):
        """ Upgrade the cluster """
        pass

    def bundle(self, user: str):
        """ Upgrade the cluster """
        self.exec(["client-config"])

    def exec(self, args):
        """ Run a launchpad command """

        cmd = [self.bin]
        cmd += args

        cmd += ["-c", self.config_file]

        exec = subprocess.run(cmd, cwd=self.working_dir)
        exec.check_returncode()
