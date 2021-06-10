"""

Run a Sonobuoy run on a k82 client.

Use this to run the sonobuoy implementation

"""
from typing import Dict, Any, List
import logging
import subprocess
import os
import json
from enum import Enum, unique

import yaml

from configerus.loaded import LOADED_KEY_ROOT
from configerus.contrib.jsonschema.validate import PLUGIN_ID_VALIDATE_JSONSCHEMA_SCHEMA_CONFIG_LABEL
from configerus.validator import ValidationError

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.fixtures import Fixtures
from mirantis.testing.metta.client import METTA_PLUGIN_TYPE_CLIENT
from mirantis.testing.metta.workload import WorkloadBase, WorkloadInstanceBase
from mirantis.testing.metta_kubernetes import (METTA_PLUGIN_ID_KUBERNETES_CLIENT,
                                               KubernetesApiClientPlugin)

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

SONODBUOY_DEFAULT_WAIT_PERIOD_SECS = 1440
""" Default time for sonobuoy to wait when running """

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
    """Workload class for the Sonobuoy"""

    def __init__(self, environment: Environment, instance_id: str,
                 label: str = SONOBUOY_WORKLOAD_CONFIG_LABEL,
                 base: Any = SONOBUOY_WORKLOAD_CONFIG_BASE):
        """Initialize workload plugin.

        Parameters:
        -----------
        label (str) : Configerus label for loading config
        base (Any) : configerus base key which should contain all of the config

        """
        self.environment = environment
        """ Environemnt in which this plugin exists """
        self.instance_id = instance_id
        """ Unique id for this plugin instance """

        logger.info("Preparing sonobuoy settings")

        self.config_label = label
        """ configerus load label that should contain all of the config """
        self.config_base = base
        """ configerus get key that should contain all tf config """

    def create_instance(self, fixtures: Fixtures):
        """Create a workload instance from a set of fixtures.

        Parameters:
        -----------
        fixtures (Fixtures) : a set of fixtures that this workload will use to
            retrieve a kubernetes api client plugin.

        """
        loaded = self.environment.config.load(self.config_label)
        """ get a configerus LoadedConfig for the sonobuoy label """

        # Validate the config overall using jsonschema
        try:
            loaded.get(self.config_base, validator=SONOBUOY_VALIDATE_TARGET)
        except ValidationError as err:
            raise ValueError("Invalid sonobuoy config received") from err

        kubeclient = fixtures.get_plugin(
            plugin_type=METTA_PLUGIN_TYPE_CLIENT, plugin_id=METTA_PLUGIN_ID_KUBERNETES_CLIENT)

        mode = loaded.get([self.config_base,
                           SONOBUOY_CONFIG_KEY_MODE])
        kubernetes_version = loaded.get(
            [self.config_base, SONOBUOY_CONFIG_KEY_KUBERNETESVERSION], default='')
        plugins = loaded.get(
            [self.config_base, SONOBUOY_CONFIG_KEY_PLUGINS], default=[])
        plugin_envs = loaded.get(
            [self.config_base, SONOBUOY_CONFIG_KEY_PLUGINENVS], default=[])

        return SonobuoyConformanceWorkloadInstance(
            kubeclient=kubeclient, mode=mode, kubernetes_version=kubernetes_version,
            plugins=plugins, plugin_envs=plugin_envs)

    # the deep argument is a standard for the info hook
    # pylint: disable=unused-argument
    def info(self, deep: bool = False):
        """Return dict data about this plugin for introspection."""
        loaded = self.environment.config.load(self.config_label)
        """ get a configerus LoadedConfig for the sonobuoy label """
        sonobuoy_config = loaded.get(self.config_base, default={})
        """ load the sonobuoy conifg (e.g. sonobuoy.yml) """

        try:
            kubeclient = self.environment.fixtures.get_plugin(
                plugin_type=METTA_PLUGIN_TYPE_CLIENT, plugin_id=METTA_PLUGIN_ID_KUBERNETES_CLIENT)
        except KeyError:
            # we will just work around a missing kube api plugin
            kubeclient = None

        info = {
            'workload': {
                'cncf': sonobuoy_config,
                'required_fixtures': {
                    'kubernetes': {
                        'plugin_type': METTA_PLUGIN_TYPE_CLIENT,
                        'plugin_id': 'metta_kubernetes',
                        'kube_client': kubeclient.info() if hasattr(kubeclient, 'info') else None
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
    """A conformance workload instance for a docker run."""

    # pylint: disable=too-many-arguments
    def __init__(self, kubeclient: KubernetesApiClientPlugin, mode: str,
                 kubernetes_version: str = '', plugins: List[str] = None,
                 plugin_envs: List[str] = None, binary: str = SONOBUOY_DEFAULT_BIN,
                 results_path: str = SONOBUOY_DEFAULT_RESULTS_PATH):
        """Imitialize the workload instance."""
        self.kubeclient = kubeclient
        """ metta kube client, which gives us a kubeconfig """
        self.mode = mode
        """ sonobuoy mode, passed to the cli """
        self.kubernetes_version = kubernetes_version
        """ Kubernetes version to test compare against """
        self.plugins = plugins if plugins is not None else []
        """ which sonobuoy plugins to run """
        self.plugin_envs = plugin_envs if plugin_envs is not None else []
        """ Plugin specific ENVs to pass to sonobuoy """

        self.bin = binary
        """ path to the sonobuoy binary """

        self.results_path = results_path
        """ path to where to download sonobuoy results """

    # These are work for this scenario
    # pylint: disable=arguments-differ
    def apply(self, wait: bool = True):
        """Run sonobuoy."""
        cmd = ['run']
        # we don't need to add --kubeconfig here as self._run() does that

        if self.mode:
            cmd += [f'--mode={self.mode}']

        if self.kubernetes_version:
            cmd += [f'--kube-conformance-image-version={self.kubernetes_version}']

        if self.plugins:
            cmd += [f'--plugin={plugin_id}' for plugin_id in self.plugins]

        if self.plugin_envs:
            cmd += [f'--plugin-env={plugin_env}' for plugin_env in self.plugin_envs]

        if wait:
            cmd += [f'--wait={SONODBUOY_DEFAULT_WAIT_PERIOD_SECS}']

        logger.info("Starting Sonobuoy run : %s", cmd)
        try:
            self._create_k8s_crb()
            self._run(cmd)
        except Exception as err:
            raise RuntimeError("Sonobuoy RUN failed") from err

    def status(self):
        """Retrieve Sonobuoy status return."""
        cmd = ['status', '--json']
        status = self._run(cmd, return_output=True)
        if status:
            return SonobuoyStatus(status)

        return None

    def logs(self, follow: bool = True):
        """Retrieve sonobuoy logs."""
        cmd = ['logs']

        if follow:
            cmd += ['--follow']

        self._run(cmd)

    def retrieve(self):
        """Retrieve sonobuoy results."""
        logger.debug("retrieving sonobuoy results")
        try:
            cmd = ['retrieve', self.results_path]
            file = self._run(cmd=cmd, return_output=True).rstrip("\n")
            if not os.path.isfile(file):
                raise RuntimeError('Sonobuoy did not retrieve a results tarball.')
            return SonobuoyResults(tarball=file, folder=self.results_path)
        except Exception as err:
            raise RuntimeError("Could not retrieve sonobuoy results") from err

    # These are work for this scenario
    # pylint: disable=arguments-differ
    def destroy(self, wait: bool = False):
        """Delete sonobuoy resources."""
        cmd = ['delete']

        if wait:
            cmd += ['--wait']

        self._run(cmd)
        self._delete_k8s_crb()

    def _run(self, cmd: List[str], ignore_errors: bool = True, return_output: bool = False):
        """Run a sonobuoy command."""
        kubeconfig = self.kubeclient.config_file
        cmd = [self.bin, f'--kubeconfig={kubeconfig}'] + cmd

        # this else makes it much more readable
        # pylint: disable=no-else-return
        if return_output:
            logger.debug(
                "running sonobuoy command with output capture: %s",
                " ".join(cmd))
            res = subprocess.run(cmd, shell=False, check=True, stdout=subprocess.PIPE)

            # sonobuoy's uses of subprocess error is overly inclusive for us
            if not ignore_errors:
                res.check_returncode()

            return res.stdout.decode('utf-8')

        else:
            logger.debug("running sonobuoy command: %s", " ".join(cmd))
            res = subprocess.run(cmd, check=True, text=True)

            if not ignore_errors:
                res.check_returncode()

            return res

    def _create_k8s_crb(self):
        """Create the cluster role binding that sonobuoy needs."""
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
            res = subprocess.run(crb_cmds, env=env, check=True, text=True)
            res.check_returncode()
            return res
        except subprocess.CalledProcessError:
            # this typically means that the CRBs already exist
            return None

    def _delete_k8s_crb(self):
        """Remove the cluster role binding that we created."""
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
        res = subprocess.run(
            crb_cmds, env=env, check=True, text=True)
        res.check_returncode()
        return res


class SonobuoyStatus:
    """A status ooutput from the sonobuoy CLI."""

    def __init__(self, status_json: str):
        """Build from sonobuoy status results."""
        status = json.loads(status_json)
        self.status = Status(status['status'])
        self.tar_info = status['tar-info']

        self.plugins = {}
        for plugin in status['plugins']:
            self.plugins[plugin['plugin']] = plugin

    def plugin_list(self):
        """Retrieve the list of plugins."""
        return list(self.plugins.keys())

    def plugin(self, plugin: str):
        """Retrieve the results for one plugin."""
        return self.plugins[plugin]

    def plugin_status(self, plugin: str):
        """Get the status code for a plugin."""
        status_string = self.plugin(plugin)['status']
        return Status(status_string)


class SonobuoyResults:
    """Results retrieved analyzer."""

    def __init__(self, tarball: str, folder: str):
        """Interpret tarball contents."""
        logger.debug("un-tarring retrieved results: %s", tarball)
        res = subprocess.run(['tar', '-xzf', tarball, '-C', folder], check=True, text=True)
        res.check_returncode()

        self.results_path = folder

        with open(os.path.join(folder, 'meta', 'config.json')) as config_json:
            self.meta_config = json.load(config_json)
        with open(os.path.join(folder, 'meta', 'info.json')) as info_json:
            self.meta_info = json.load(info_json)
        with open(os.path.join(folder, 'meta', 'query-time.json')) as qt_json:
            self.meta_querytime = json.load(qt_json)

        self.plugins = []
        for plugin_id in self.meta_info['plugins']:
            self.plugins.append(plugin_id)

    def plugin_list(self):
        """Return a string list of plugin ids."""
        return self.plugins

    def plugin(self, plugin_id):
        """Return the results for a single plugin."""
        return SonobuoyResultsPlugin(os.path.join(
            self.results_path, 'plugins', plugin_id))


class SonobuoyResultsPlugin:
    """The full results for a plugin."""

    def __init__(self, path: str):
        """Load results for a plugin results call."""
        with open(os.path.join(path, 'sonobuoy_results.yaml')) as results_yaml:
            self.summary = yaml.safe_load(results_yaml)

    def name(self) -> str:
        """Return string name of plugin."""
        return self.summary['name']

    def status(self) -> "Status":
        """Return the status object for the plugin results."""
        return Status(self.summary['status'])

    def __len__(self):
        """Count how many items are in the plugin_results."""
        return len(self.summary['items'])

    def __getitem__(self, instance_id: Any) -> object:
        """Get item details from the plugin results."""
        return SonobuoyResultsPluginItem(
            item_dict=self.summary['items'][instance_id])


class SonobuoyResultsPluginItem:
    """An individual item from a sonobuoy results plugin."""

    def __init__(self, item_dict: Dict[str, Any]):
        """Single plugin result item."""
        self.name = item_dict['name']
        self.status = Status(item_dict['status'])
        self.meta = item_dict['meta']
        self.details = item_dict['details'] if 'details' in item_dict else {}

    def meta_file_path(self):
        """Get the path to the error item file."""
        return self.meta['file']

    def meta_file(self):
        """Get the contents of the file."""
        with open(self.meta_file_path()) as meta_file:
            return yaml.safe_load(meta_file)


@unique
class Status(Enum):
    """Enumerator to plugin states."""

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
    POSTPROCESS = 'post-processing'
    """ testing has finished and is being processed """
