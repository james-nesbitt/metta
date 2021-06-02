"""

Helm workload Metta plugin

As a workload, using a kube_api client, manage helm charts

"""
from typing import Any, List, Dict
import logging
import subprocess
from enum import Enum

import yaml

from mirantis.testing.metta.fixtures import Fixtures
from mirantis.testing.metta.client import METTA_PLUGIN_TYPE_CLIENT
from mirantis.testing.metta.workload import WorkloadBase

from .kubeapi_client import METTA_PLUGIN_ID_KUBERNETES_CLIENT

logger = logging.getLogger('metta.contrib.kubernetes.workload.helm')

METTA_PLUGIN_ID_KUBERNETES_HELM_WORKLOAD = 'metta_kubernetes_helm'
""" workload plugin_id for the metta_kubernetes helm plugin """


KUBERNETES_HELM_WORKLOAD_CONFIG_LABEL = 'kubernetes'
""" default config label used to load the workload """
KUBERNETES_HELM_WORKLOAD_CONFIG_BASE = 'workload.helm'
""" default config key for creating a workload object """

KUBERNETES_HELM_WORKLOAD_CONFIG_KEY_VERSION = 'version'
""" config key for helm version """
KUBERNETES_HELM_WORKLOAD_CONFIG_KEY_REPOS = 'repos'
""" config key for helm repos dict which need to be added """
KUBERNETES_HELM_WORKLOAD_CONFIG_KEY_CHART = 'chart'
""" config key for helm chart, either local path or http(s) """
KUBERNETES_HELM_WORKLOAD_CONFIG_KEY_VALUESSET = 'set'
""" config key for helm chart values """
KUBERNETES_HELM_WORKLOAD_CONFIG_KEY_VALUESFILE_VALUES = 'values'
""" config key for helm chart values that should be put into a values file """
KUBERNETES_HELM_WORKLOAD_CONFIG_KEY_VALUESFILE_PATH = 'file'
""" config key for helm chart path to values file that we should create """
KUBERNETES_HELM_WORKLOAD_CONFIG_DEFAULT_VALUESFILE_PATH = 'values.yml'
""" config default value for helm chart path to values file that we should create """
KUBERNETES_HELM_WORKLOAD_CONFIG_KEY_NAMESPACE = 'namespace'
""" config key for namespace to install to """

KUBERNETES_HELM_WORKLOAD_DEFAULT_NAMESPACE = 'default'
""" default namespace to install to if no namespace was passed """

KUBERNETES_HELM_WORKLOAD_DEFAULT_BIN = 'helm'
""" default helm executble path """
KUBERNETES_HELM_WORKLOAD_DEFAULT_WORKINGDIR = '.'
""" default helm working dir for subprocess """


class KubernetesHelmWorkloadPlugin(WorkloadBase):
    """Kubernetes workload class."""

    def __init__(self, environment, instance_id, label: str = KUBERNETES_HELM_WORKLOAD_CONFIG_LABEL,
                 base: Any = KUBERNETES_HELM_WORKLOAD_CONFIG_BASE):
        """Run the super constructor but also set class properties.

        This implements the args part of the client interface.

        Here we expect to receiv config pointers so that we can determine what
        helm workload to apply, and what values will be needed.

        Parameters:
        -----------
        config_file (str): String path to the kubernetes config file to use

        """
        self.environment = environment
        """ Environemnt in which this plugin exists """
        self.instance_id = instance_id
        """ Unique id for this plugin instance """

        self.config_label = label
        """ configerus load label that should contain all of the config """
        self.config_base = base
        """ configerus get key that should contain all tf config """

    def create_instance(self, fixtures: Fixtures):
        """Create a workload instance from a set of fixtures.

        Parameters:
        -----------
        fixtures (Fixtures) : a set of fixtures that this workload will use to
            retrieve a kubernetes client plugin.

        """
        try:
            client = fixtures.get_plugin(plugin_type=METTA_PLUGIN_TYPE_CLIENT,
                                         plugin_id=METTA_PLUGIN_ID_KUBERNETES_CLIENT)
        except KeyError as err:
            raise NotImplementedError("Workload could not find the needed client: "
                                      f"{METTA_PLUGIN_ID_KUBERNETES_CLIENT}") from err

        workload_config = self.environment.config.load(self.config_label)

        kubeconfig = client.config_file

        namespace = workload_config.get(
            [self.config_base, KUBERNETES_HELM_WORKLOAD_CONFIG_KEY_NAMESPACE],
            default=KUBERNETES_HELM_WORKLOAD_DEFAULT_NAMESPACE)

        chart = workload_config.get(
            [self.config_base, KUBERNETES_HELM_WORKLOAD_CONFIG_KEY_CHART])

        values_set = workload_config.get(
            [self.config_base, KUBERNETES_HELM_WORKLOAD_CONFIG_KEY_VALUESSET], default={})
        values = workload_config.get(
            [self.config_base, KUBERNETES_HELM_WORKLOAD_CONFIG_KEY_VALUESFILE_VALUES], default={})
        file = workload_config.get(
            [self.config_base, KUBERNETES_HELM_WORKLOAD_CONFIG_KEY_VALUESFILE_PATH],
            default=KUBERNETES_HELM_WORKLOAD_CONFIG_DEFAULT_VALUESFILE_PATH)

        repos = workload_config.get(
            [self.config_base, KUBERNETES_HELM_WORKLOAD_CONFIG_KEY_REPOS], default={})

        return KubernetesHelmV3WorkloadInstance(
            kubeconfig=kubeconfig, namespace=namespace, name=self.instance_id, repos=repos,
            chart=chart, values_set=values_set, values=values, file=file)

    def info(self):
        """Return dict data about this plugin for introspection."""
        workload_config = self.environment.config.load(self.config_label)

        return {
            'workload': {
                'deployment': {
                    'repos': workload_config.get(
                        [self.config_base, KUBERNETES_HELM_WORKLOAD_CONFIG_KEY_REPOS]),
                    'chart': workload_config.get(
                        [self.config_base, KUBERNETES_HELM_WORKLOAD_CONFIG_KEY_CHART]),
                    'set': workload_config.get(
                        [self.config_base, KUBERNETES_HELM_WORKLOAD_CONFIG_KEY_VALUESSET]),
                    'values': workload_config.get(
                        [self.config_base, KUBERNETES_HELM_WORKLOAD_CONFIG_KEY_VALUESFILE_VALUES])
                },
                'required_fixtures': {
                    'kubernetes': {
                        'plugin_type': METTA_PLUGIN_TYPE_CLIENT,
                        'plugin_id': 'metta_kubernetes'
                    }
                }
            }
        }


# This is how many vars it takes to program helm
# pylint: disable=too-many-instance-attributes
class KubernetesHelmV3WorkloadInstance:
    """A workload instance, which is a single active helm chart.

    A workload plugin can create many isntances.

    """

    # pylint: disable=too-many-arguments
    def __init__(self, kubeconfig, namespace, name, repos, chart, values_set: Dict[str, str] = None,
                 values: Dict[str, Any] = None,
                 helm_bin: str = KUBERNETES_HELM_WORKLOAD_DEFAULT_BIN,
                 file: str = KUBERNETES_HELM_WORKLOAD_CONFIG_DEFAULT_VALUESFILE_PATH,
                 work_dir: str = KUBERNETES_HELM_WORKLOAD_DEFAULT_WORKINGDIR):
        """Set initial instance state.

        Parameters:
        -----------
        kubeconfig (str) : Path to the kubeinfo file

        repos (dict[str, str]) : name->path for repos to add

        chart (str) : local or http(s) path to a chart

        value_set (dict[str, str]) : simple helm chart values that can be set using
           the --set options on the command line

        values (dict[str, Any]) : complex helm chart value data that needs to
            be put into a file
        file (str) : path to where we should put values yaml file

        bin (str) : helm executable path
        dir (dir) : working dir to be used with subprocess

        """
        self.kubeconfig = kubeconfig
        self.name = name
        self.namespace = namespace
        self.repos = repos
        self.chart = chart

        self.set = values_set if values_set is not None else {}
        self.values = values if values is not None else {}
        self.file = file

        self.bin = helm_bin
        self.working_dir = work_dir

    def apply(self, wait: bool = True, debug: bool = False):
        """Apply the helm chart.

        To make the helm apply method reusable, we always run an upgrade with
        the --install flag, which w orks for both the first install, and any
        upgrades run after install

        Parameters:
        -----------
        wait (bool) : ask the helm client to wait until resources are created
            before returning.

        debug (bool) : ask the helm client for verbose output

        """
        for repo_name, repo_url in self.repos.items():
            self._run(cmd=['repo', 'add', repo_name, repo_url])

        cmd = ['upgrade']
        cmd += [self.name, self.chart]

        cmd += ['--install', '--create-namespace']

        if wait:
            cmd += ['--wait']
        if debug:
            cmd += ['--debug']

        if len(self.set):
            # turn the set dict into '--set a=A,b=B,c=C'
            cmd += ['--set', ','.join([f"{name}={value}" for (name, value) in self.values.items()])]

        if len(self.values):
            # turn the values into a file, and add it to the command
            with open(self.file, 'w') as val_file:
                yaml.dump(self.values, val_file)

            cmd += ['--values', self.file]

        try:
            self._run(cmd=cmd)
        except Exception as err:
            raise RuntimeError("Helm failed to install the relese") from err

    # -all is the used command flag, so the var name makes sense
    # pylint: disable=redefined-builtin
    def list(self, all: bool = False, failed: bool = False,
             deployed: bool = False, pending: bool = False):
        """List all releases.

        This is not instance specific but still useful.

        """
        cmd = ['list', '--output=yaml']

        if all:
            cmd += ['--all']
        elif deployed:
            cmd += ['--deployed']
        elif failed:
            cmd += ['--failed']
        elif pending:
            cmd += ['--pending']

        list_str = self._run(cmd=cmd, return_output=True)
        if list_str:
            return yaml.safe_load(list_str)

        return []

    def destroy(self, debug: bool = False):
        """Remove an installed helm release.

        Parameters:
        -----------
        debug (bool) : ask the helm client for verbose output

        """
        cmd = ['uninstall', self.name]

        if debug:
            cmd += ['--debug']

        self._run(cmd=cmd)

    def test(self):
        """Test an installed helm release.

        This runs the helm client test command.

        """
        self._run(cmd=['test', self.name])

    def status(self):
        """Get status of the installed helm release."""
        return HelmReleaseStatus(yaml.safe_load(
            self._run(cmd=['status', self.name, '--output', 'yaml'], return_output=True)))

    def _run(self, cmd: List[str], return_output: bool = False):
        """Run a helm v3 command."""
        cmd = [self.bin, f'--kubeconfig={self.kubeconfig}', f'--namespace={self.namespace}'] + cmd

        # this syntax makes it easier to read
        # pylint: disable=no-else-return
        if return_output:
            logger.debug("running launchpad command with output capture: %s", " ".join(cmd))
            exec = subprocess.run(cmd, cwd=self.working_dir, shell=False, check=True,
                                  stdout=subprocess.PIPE)
            exec.check_returncode()
            return exec.stdout.decode('utf-8')
        else:
            logger.debug("running launchpad command: %s", " ".join(cmd))
            exec = subprocess.run(cmd, cwd=self.working_dir, check=True, text=True)
            exec.check_returncode()
            return exec


class Status(Enum):
    """A Helm Status enum."""

    DEPLOYED = 'deployed'
    """ Helm Release has been deployed """


# This is effectively a struct for interpreting the release status information
# pylint: disable=too-few-public-methods
class HelmReleaseStatus:
    """Interpreted helm release status.

    Used to formalize the response object from a status request

    """

    def __init__(self, status_reponse: dict):
        """Interpret status from a status response."""
        self.name = status_reponse['name']
        self.version = status_reponse['version']
        self.namespace = status_reponse['namespace']

        # self.first_deployed = datetime.strptime(status_reponse['info']['first_deployed'],
        #                                         '%Y-%m-%dT%H:%M:%S.%fZ')
        # self.last_deployed = datetime.strptime(status_reponse['info']['last_deployed'],
        #                                         '%Y-%m-%dT%H:%M:%S.%fZ')

        self.deleted = status_reponse['info']['deleted']
        self.description = status_reponse['info']['description']
        self.status = Status(status_reponse['info']['status'])
        self.notes = status_reponse['info']['notes']

        self.config = status_reponse['config']

        self.manifect = status_reponse['manifest']
