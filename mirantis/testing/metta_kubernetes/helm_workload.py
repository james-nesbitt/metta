from typing import Any, List
import logging
import os
import subprocess

import kubernetes

from mirantis.testing.metta.plugin import Type
from mirantis.testing.metta.fixtures import Fixtures
from mirantis.testing.metta.workload import WorkloadBase

logger = logging.getLogger('metta.contrib.kubernetes.workload.helm')


class HelmWorkloadPlugin(WorkloadBase):
    """ Helm client for interacting with a kube client """


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
KUBERNETES_HELM_WORKLOAD_CONFIG_KEY_VALUES = 'values'
""" config key for helm chart values """


class KubernetesHelmWorkloadPlugin(WorkloadBase):
    """ Kubernetes workload class """

    def __init__(self, environment, instance_id,
                 label: str = KUBERNETES_HELM_WORKLOAD_CONFIG_LABEL, base: Any = KUBERNETES_HELM_WORKLOAD_CONFIG_BASE):
        """ Run the super constructor but also set class properties

        This implements the args part of the client interface.

        Here we expect to receiv config pointers so that we can determine what
        helm workload to apply, and what values will be needed.

        Parameters:
        -----------

        config_file (str): String path to the kubernetes config file to use

        """
        WorkloadBase.__init__(self, environment, instance_id)

        self.config_label = label
        """ configerus load label that should contain all of the config """
        self.config_base = base
        """ configerus get key that should contain all tf config """

    def create_instance(self, fixtures: Fixtures):
        """ Create a workload instance from a set of fixtures

        Parameters:
        -----------

        fixtures (Fixtures) : a set of fixtures that this workload will use to
            retrieve a kubernetes client plugin.

        """

        try:
            client = fixtures.get_plugin(
                type=Type.CLIENT, plugin_id='metta_kubernetes')
        except KeyError as e:
            raise NotImplementedError(
                "Workload could not find the needed client: {}".format('metta_kubernetes'))

        workload_config = self.environment.config.load(self.config_label)

        kubeconfig = client.config_file

        chart = workload_config.get(
            [self.config_base, KUBERNETES_HELM_WORKLOAD_CONFIG_KEY_CHART], exception_if_missing=True)

        values = workload_config.get(
            [self.config_base, KUBERNETES_HELM_WORKLOAD_CONFIG_KEY_VALUES], exception_if_missing=False)
        if values is None:
            values = {}

        repos_config = workload_config.get(
            [self.config_base, KUBERNETES_HELM_WORKLOAD_CONFIG_KEY_REPOS], exception_if_missing=False)
        if repos_config is None:
            repos_config = {}

        return KubernetesHelmV3WorkloadInstance(
            kubeconfig, self.instance_id, repos_config, chart, values)

    def info(self):
        """ Return dict data about this plugin for introspection """
        workload_config = self.environment.config.load(self.config_label)

        return {
            'workload': {
                'deployment': {
                    'repos_config': workload_config.get(
                        [self.config_base, KUBERNETES_HELM_WORKLOAD_CONFIG_KEY_REPOS]),
                    'chart': workload_config.get(
                        [self.config_base, KUBERNETES_HELM_WORKLOAD_CONFIG_KEY_CHART]),
                    'values': workload_config.get(
                        [self.config_base, KUBERNETES_HELM_WORKLOAD_CONFIG_KEY_VALUES])
                },
                'required_fixtures': {
                    'kubernetes': {
                        'type': Type.CLIENT.value,
                        'plugin_id': 'metta_kubernetes'
                    }
                }
            }
        }


class KubernetesHelmV3WorkloadInstance:

    def __init__(self, kubeconfig, name, repos_config, chart, values):
        """

        Parameters:
        -----------

        kubeconfig (str) : Path to the kubeinfo file

        repos_config (dict[str, str]) : name->path for repos to add

        chart (str) : local or http(s) path to a chart

        values (dict[str, Any]) : helm chart values

        """

        self.kubeconfig = kubeconfig
        self.name = name
        self.repos_config = repos_config
        self.chart = chart
        self.values = values

        self.bin = 'helm'
        self.working_dir = '.'

    def apply(self):
        """ Apply the helm chart """

        for repo_name, repo_url in self.repos_config.items():
            self._run(cmd=['repo', 'add', repo_name, repo_url])

        if len(self.values):
            # turn the values dict into '--set a=A,b=B,c=C'
            values = ['--set', ','.join(['{}={}'.format(name, value)
                                         for (name, value) in self.values.items()])]
        else:
            values = []

        cmd = ['install'] + values + [self.name, self.chart]
        self._run(cmd=cmd)

    def destroy(self):
        """ remove an installed helm release """
        self._run(cmd=['uninstall', self.name])

    def _run(self, cmd: List[str], return_output: bool = False):
        """ run a helm v3 command """

        env = os.environ.copy()
        env['KUBECONFIG'] = self.kubeconfig

        cmd = [self.bin] + cmd

        if return_output:
            logger.debug(
                "running launchpad command with output capture: %s",
                " ".join(cmd))
            exec = subprocess.run(
                cmd,
                cwd=self.working_dir,
                shell=False,
                stdout=subprocess.PIPE)
            exec.check_returncode()
            return exec.stdout.decode('utf-8')
        else:
            logger.debug("running launchpad command: %s", " ".join(cmd))
            exec = subprocess.run(
                cmd, cwd=self.working_dir, check=True, text=True)
            exec.check_returncode()
