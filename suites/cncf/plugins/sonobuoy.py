"""

Run a Sonobuoy run on a k82 client 

@Note this will run the sonobuoy implementation

"""
from typing import Dict, Any
import logging
import subprocess

from configerus.loaded import LOADED_KEY_ROOT

from mirantis.testing.metta.plugin import Type
from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.fixtures import Fixtures
from mirantis.testing.metta.workload import WorkloadBase, WorkloadInstanceBase
from mirantis.testing.metta_kubernetes import METTA_PLUGIN_ID_KUBERNETES_CLIENT

logger = logging.getLogger('workload.sonobuoy')

SONOBUOY_WORKLOAD_CONFIG_LABEL = 'sonobuoy'
""" Configerus label for retrieving sonobuoy config """
SONOBUOY_WORKLOAD_CONFIG_BASE = LOADED_KEY_ROOT
""" Configerus get base for retrieving the default workload config """


class SonobuoyWorkloadPlugin(WorkloadBase):
    """ Workload class for the Sonobuoy """

    def __init__(self, environment: Environment, instance_id: str,
                 label: str = SONOBUOY_WORKLOAD_CONFIG_LABEL, base: Any = SONOBUOY_WORKLOAD_CONFIG_BASE):
        """ Run the super constructor but also set class properties

        Parameters:
        -----------

        label (str) : Configerus label for loading config
        base (Any) : configerus base key which should contain all of the config

        """
        WorkloadBase.__init__(self, environment, instance_id)

        logger.info("Preparing sonobuoy settings")

        self.config_label = label
        """ configerus load label that should contain all of the config """
        self.config_base = base
        """ configerus get key that should contain all tf config """

    def create_instance(self, fixtures: Fixtures):
        """ Create a workload instance from a set of fixtures

        Parameters:
        -----------

        fixtures (Fixtures) : a set of fixtures that this workload will use to
            retrieve a docker client plugin.

        """

        client = fixtures.get_plugin(
            type=Type.CLIENT, plugin_id=METTA_PLUGIN_ID_KUBERNETES_CLIENT)

        loaded = self.environment.config.load(self.config_label)
        """ get a configerus LoadedConfig for the sonobuoy label """
        
        sonobuoy_config = loaded.get([self.config_base, self.config_base],
                             exception_if_missing=True)
        

        return DockerRunWorkloadInstance(client, run)

    def info(self):
        """ Return dict data about this plugin for introspection """

        loaded = self.environment.config.load(self.config_label)
        """ get a configerus LoadedConfig for the sonobuoy label """
        
        sonobuoy_config = loaded.get([self.config_base, self.config_base],
                             exception_if_missing=True)

        return {
            'workload': {
                'cncf': sonobuoy_config,
                'required_fixtures': {
                    'kubernetes': {
                        'type': Type.CLIENT.value,
                        'plugin_id': 'metta_kubernetes'
                    }
                }
            }
        }

SONOBUOY_BIN = 'sonobuoy'
SONOBUOY_PACKAGE = 'https://github.com/vmware-tanzu/sonobuoy/releases/download/v0.20.0/sonobuoy_0.20.0_linux_amd64.tar.gz'

class SonobuoyConformanceWorkloadInstance(WorkloadInstanceBase):
    """ A conformance workload instance for a docker run """

    def __init__(self, kubeconfig: str, mode:str, kubernetes_version: str, plugin_env: List[str]):
        self.kubeconfig = kubeconfig
        self.mode = mode 
        self.kubernetes_version = kubernetes_version 
        self.plugin_env = plugin_env

        self.bin = SONOBUOY_BIN

    def run(self):
        """ run sonobuoy """
        cmd = ['run']

        cmd += ['--mode="{}"'.format(self.mode)]
        cmd += ['--kube-conformance-image="{}"'.format(self.kubernetes_version)]

        for env in self.plugin_env
        self._run(cmd)


    def _run(self, cmd: List[str], return_output: bool = False):
        """ run a sonobuoy command """"

        env = os.environ.copy()
        env['KUBECONFIG'] = self.kubeconfig

        cmd = [self.bin] + cmd

        if return_output:
            logger.debug(
                "running sonobuoy command with output capture: %s",
                " ".join(cmd))
            exec = subprocess.run(
                cmd,
                env=env,
                cwd=self.working_dir,
                shell=False,
                stdout=subprocess.PIPE)
            exec.check_returncode()
            return exec.stdout.decode('utf-8')
        else:
            logger.debug("running sonobuoy command: %s", " ".join(cmd))
            exec = subprocess.run(
                cmd, env=env, cwd=self.working_dir, check=True, text=True)
            exec.check_returncode()
            return exec
