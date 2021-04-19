"""

Run a Sonobuoy run on a k82 client

@Note this will run the sonobuoy implementation

"""
from typing import Dict, Any, List
import logging
import subprocess
import os
import json
import yaml
from enum import Enum, unique

from configerus.loaded import LOADED_KEY_ROOT
from configerus.contrib.jsonschema.validate import PLUGIN_ID_VALIDATE_JSONSCHEMA_SCHEMA_CONFIG_LABEL
from configerus.validator import ValidationError

from mirantis.testing.metta.plugin import Type
from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.fixtures import Fixtures
from mirantis.testing.metta.workload import WorkloadBase, WorkloadInstanceBase
from mirantis.testing.metta_kubernetes import METTA_PLUGIN_ID_KUBERNETES_CLIENT

logger = logging.getLogger('workload.sonobuoy')

METTA_PLUGIN_ID_SONOBUOY_WORKLOAD = 'metta_sonobuoy_workload'
""" workload plugin_id for the sonobuoy plugin """

SONOBUOY_WORKLOAD_CONFIG_LABEL = 'sonobuoy'
""" Configerus label for retrieving sonobuoy config """
SONOBUOY_WORKLOAD_CONFIG_BASE = LOADED_KEY_ROOT
""" Configerus get base for retrieving the default workload config """

SONOBUOY_CONFIG_KEY_MODE = 'mode'
""" config key for mode """
SONOBUOY_CONFIG_KEY_KUBERNETESVERSION = 'kubernetes.version'
""" config key for kubernetes version """
SONOBUOY_CONFIG_KEY_PLUGINS = 'plugin.plugins'
""" config key for what plugins to run """
SONOBUOY_CONFIG_KEY_PLUGINENVS = 'plugin.envs'
""" config key for plugin env flags """

SONOBUOY_VALIDATE_JSONSCHEMA = {
    'type': 'object',
    'properties': {
        'type': {'type': 'string'},
        'plugin_id': {'type': 'string'},

        'mode': {
            'type': 'string'
        },
        'kubernetes': {
            'type': 'object',
            'properties': {
                'version': {'type': 'string'}
            },
        },
        'kubernetes_version': {
            'type': 'string'
        },
        'plugin': {
            'type': 'object',
            'properties': {
                'plugins': {
                    'type': 'array',
                    'items': {
                        'type': 'string'
                    }
                },
                'plugin_envs': {
                    'type': 'array',
                    'items': {
                        'type': 'string'
                    }
                }
            }
        },
    },
    'required': ['mode', 'kubernetes']
}
""" Validation jsonschema for terraform config contents """
SONOBUOY_VALIDATE_TARGET = {
    PLUGIN_ID_VALIDATE_JSONSCHEMA_SCHEMA_CONFIG_LABEL: SONOBUOY_VALIDATE_JSONSCHEMA}
""" configerus validation target to match the jsonschema config """


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
            retrieve a kubernetes api client plugin.

        """

        loaded = self.environment.config.load(self.config_label)
        """ get a configerus LoadedConfig for the sonobuoy label """

        # Validate the config overall using jsonschema
        try:
            sonobuoy_config = loaded.get(
                self.config_base,
                validator=SONOBUOY_VALIDATE_TARGET)
        except ValidationError as e:
            raise ValueError(
                "Invalid sonobuoy config received: {}".format(e)) from e

        kubeclient = fixtures.get_plugin(
            type=Type.CLIENT, plugin_id=METTA_PLUGIN_ID_KUBERNETES_CLIENT)

        mode = loaded.get([self.config_base,
                           SONOBUOY_CONFIG_KEY_MODE])
        kubernetes_version = loaded.get(
            [self.config_base, SONOBUOY_CONFIG_KEY_KUBERNETESVERSION], default='')
        plugins = loaded.get(
            [self.config_base, SONOBUOY_CONFIG_KEY_PLUGINS], default=[])
        plugin_envs = loaded.get(
            [self.config_base, SONOBUOY_CONFIG_KEY_PLUGINENVS], default=[])

        return SonobuoyConformanceWorkloadInstance(
            kubeclient=kubeclient, mode=mode, kubernetes_version=kubernetes_version, plugins=plugins, plugin_envs=plugin_envs)

    def info(self, deep: bool = False):
        """ Return dict data about this plugin for introspection """

        loaded = self.environment.config.load(self.config_label)
        """ get a configerus LoadedConfig for the sonobuoy label """

        sonobuoy_config = loaded.get(self.config_base)

        kubeclient = self.environment.fixtures.get_plugin(
            type=Type.CLIENT, plugin_id=METTA_PLUGIN_ID_KUBERNETES_CLIENT)

        info = {
            'workload': {
                'cncf': sonobuoy_config,
                'kube_client': kubeclient.info(),
                'required_fixtures': {
                    'kubernetes': {
                        'type': Type.CLIENT.value,
                        'plugin_id': 'metta_kubernetes'
                    }
                }
            }
        }

        return info


SONOBUOY_DEFAULT_BIN = 'sonobuoy'
""" Default Bin Name for running sonobuoy """
SONOBUOY_DEFAULT_RESULTS_PATH = './results'
""" Default path for where to download sonobuoy results """


class SonobuoyConformanceWorkloadInstance(WorkloadInstanceBase):
    """ A conformance workload instance for a docker run """

    def __init__(self, kubeclient: object, mode: str, kubernetes_version: str = '',
                 plugins: List[str] = [], plugin_envs: List[str] = [], bin: str = SONOBUOY_DEFAULT_BIN, results_path: str = SONOBUOY_DEFAULT_RESULTS_PATH):
        self.kubeclient = kubeclient
        """ metta kube client, from which we will pull the KUBECONFIG target """
        self.mode = mode
        """ sonobuoy mode, passed to the cli """
        self.kubernetes_version = kubernetes_version
        """ Kubernetes version to test compare against """
        self.plugins = plugins
        """ which sonobuoy plugins to run """
        self.plugin_envs = plugin_envs
        """ Plugin specific ENVs to pass to sonobuoy """

        self.bin = bin
        """ path to the sonobuoy binary """

        self.results_path = results_path
        """ path to where to download sonobuoy results """

    def run(self, wait: bool = True):
        """ run sonobuoy """

        cmd = ['run']
        # we don't need to add --kubeconfig here as self._run() does that

        if self.mode:
            cmd += ['--mode={}'.format(self.mode)]

        if self.kubernetes_version:
            cmd += ['--kube-conformance-image-version={}'.format(
                self.kubernetes_version)]

        if self.plugins:
            cmd += ['--plugin={}'.format(plugin_id)
                    for plugin_id in self.plugins]

        if self.plugin_envs:
            cmd += ['--plugin-env={}'.format(plugin_env)
                    for plugin_env in self.plugin_envs]

        if wait:
            cmd += ['--wait={}'.format(1440)]

        logger.info("Starting Sonobuoy run : {}".format(cmd))
        try:
            self._create_k8s_crb()
            self._run(cmd)
        except Exception as e:
            raise RuntimeError("Sonobuoy RUN failed: {}".format(e)) from e

    def status(self):
        """ sonobuoy status return """
        cmd = ['status', '--json']
        status = self._run(cmd, return_output=True)
        if status:
            return SonobuoyStatus(json.loads(status))
        else:
            return None

    def logs(self, follow: bool = True):
        """ sonobuoy logs """
        cmd = ['logs']

        if follow:
            cmd += ['--follow']

        self._run(cmd)

    def retrieve(self):
        """ retrieve sonobuoy results """
        logger.debug("retrieving sonobuoy results")
        try:
            cmd = ['retrieve', self.results_path]
            file = self._run(cmd=cmd, return_output=True).rstrip("\n")
            if not os.path.isfile(file):
                raise RuntimeError(
                    'Sonobuoy did not retrieve a results tarball.')
            return SonobuoyResults(tarball=file, folder=self.results_path)
        except Exception as e:
            raise RuntimeError(
                "Could not retrieve sonobuoy results: {}".format(e)) from e

    def destroy(self, wait: bool = False):
        """ delete sonobuoy resources """
        cmd = ['delete']

        if wait:
            cmd += ['--wait']

        self._run(cmd)
        self._delete_k8s_crb()

    def _run(self, cmd: List[str], ignore_errors: bool = True,
             return_output: bool = False):
        """ run a sonobuoy command """

        kubeconfig = self.kubeclient.config_file
        cmd = [self.bin, '--kubeconfig={}'.format(kubeconfig)] + cmd

        if return_output:
            logger.debug(
                "running sonobuoy command with output capture: %s",
                " ".join(cmd))
            exec = subprocess.run(
                cmd,
                shell=False,
                stdout=subprocess.PIPE)

            # sonobuoy's uses of subprocess error is overly inclusive for us
            if not ignore_errors:
                exec.check_returncode()

            return exec.stdout.decode('utf-8')
        else:
            logger.debug("running sonobuoy command: %s", " ".join(cmd))
            exec = subprocess.run(
                cmd, check=True, text=True)

            if not ignore_errors:
                exec.check_returncode()

            return exec

    def _create_k8s_crb(self):
        """ create the cluster role binding that sonobuoy needs """
        # Sonobuoy requires an admin cluster role binding
        # @TODO Do this with the kubectl client properly
        crb_cmds = [
            'kubectl',
            'create',
            'clusterrolebinding',
            'sonobuoy-serviceaccount-cluster-admin',
            '--clusterrole=cluster-admin',
            '--serviceaccount=sonobuoy:sonobuoy-serviceaccount']
        env = os.environ.copy()
        env['KUBECONFIG'] = self.kubeclient.config_file
        logger.debug(
            "creating sonobuoy cluster_role_binding: %s",
            " ".join(crb_cmds))
        try:
            exec = subprocess.run(crb_cmds, env=env, check=True, text=True)
            # exec.check_returncode()
        except BaseException:
            pass

    def _delete_k8s_crb(self):
        """ create the cluster role binding that sonobuoy needs """
        # @TODO Do this with the kubectl client properly
        crb_cmds = [
            'kubectl',
            'delete',
            'clusterrolebinding',
            'sonobuoy-serviceaccount-cluster-admin']
        env = os.environ.copy()
        env['KUBECONFIG'] = self.kubeclient.config_file
        logger.debug(
            "creating sonobuoy cluster_role_binding: %s",
            " ".join(crb_cmds))
        exec = subprocess.run(
            crb_cmds, env=env, check=True, text=True)
        exec.check_returncode()


class SonobuoyStatus:
    """ a status ooutput from the sonobuoy CLI """

    def __init__(self, status: object):
        """ build from sonobuoy status results """
        self.status = Status(status['status'])
        self.tar_info = status['tar-info']

        self.plugins = {}
        for plugin in status['plugins']:
            self.plugins[plugin['plugin']] = plugin

    def plugin_list(self):
        """ retrieve the list of plugins """
        return list(self.plugins.keys())

    def plugin(self, plugin: str):
        """ retrieve the results for one plugin """
        return self.plugins[plugin]

    def plugin_status(self, plugin: str):
        """ get the status code for a plugin """
        status_string = self.plugin(plugin)['status']
        return Status(status_string)


class SonobuoyResults:
    """ Results retrieved analyzer """

    def __init__(self, tarball: str, folder: str):
        """  interpret tarball contents """

        base = os.path.splitext(tarball)[0]

        logger.debug("un-tarring retrieved results: {}".format(tarball))
        exec = subprocess.run(
            ['tar', '-xzf', tarball, '-C', folder], check=True, text=True)
        exec.check_returncode()

        self.results_path = folder

        with open(os.path.join(folder, 'meta', 'config.json')) as f:
            self.meta_config = json.load(f)
        with open(os.path.join(folder, 'meta', 'info.json')) as f:
            self.meta_info = json.load(f)
        with open(os.path.join(folder, 'meta', 'query-time.json')) as f:
            self.meta_querytime = json.load(f)

        self.plugins = []
        for plugin_id in self.meta_info['plugins']:
            self.plugins.append(plugin_id)

    def plugin_list(self):
        """ return a string list of plugin ids """
        return self.plugins

    def plugin(self, plugin_id):
        """ return the results for a single plugin """
        return SonobuoyResultsPlugin(os.path.join(
            self.results_path, 'plugins', plugin_id))


class SonobuoyResultsPlugin:
    """ the full results for a plugin """

    def __init__(self, path: str):
        """ load results for a plugin """
        with open(os.path.join(path, 'sonobuoy_results.yaml')) as f:
            self.summary = yaml.safe_load(f)

    def name(self) -> str:
        """ return string name of plugin """
        return self.summary['name']

    def status(self) -> "Status":
        """ return the status object for the plugin """
        return Status(self.summary['status'])

    def __len__(self):
        """ How many items are in the plugin_results """
        return len(self.summary['items'])

    def __getitem__(self, instance_id: Any) -> object:
        """ get item details from the plugin results """
        return SonobuoyResultsPluginItem(
            item_dict=self.summary['items'][instance_id])


class SonobuoyResultsPluginItem:
    """ An individual item from a sonobuoy results plugin """

    def __init__(self, item_dict: Dict[str, Any]):
        """ Single plugin result item """
        self.name = item_dict['name']
        self.status = Status(item_dict['status'])
        self.meta = item_dict['meta']
        self.details = item_dict['details'] if 'details' in item_dict else {}

    def meta_file_path(self):
        """ get the path to the error item file """
        return self.meta['file']

    def meta_file(self):
        """ get the contents of the file """
        with open(self.meta_file_path()) as f:
            return yaml.safe_load(f)


@unique
class Status(Enum):
    """ Enumerator to plugin states """
    PENDING = 'pending'
    """ still pending """
    RUNNING = 'running'
    """ testing is running """
    FAILED = 'failed'
    """ testing has failed """
    COMPLETE = 'complete'
    """ testing has completed without failure """
    PASSED = 'passed'
    """ testing has passed """
