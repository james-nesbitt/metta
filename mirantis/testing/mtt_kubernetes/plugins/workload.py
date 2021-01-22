"""

Kubernetes workload plugins

"""

import logging
from typing import List

from kubernetes import utils as kubernetes_utils

from mirantis.testing.mtt.workload import WorkloadBase

from .client import KubernetesClientPlugin

logger = logging.getLogger('mirantis.testing.mtt_kubernetes.workload')

class KubernetesSpecFilesWorkloadPlugin(WorkloadBase):
    """ Dummy workload class """

    def args(files: List[str]):
        """ include a list of kubernetes yaml files to be used in this workload """
        self.files = files

    def apply(client:KubernetesClientPlugin):
        """ exec the workload on a client """
        for file in self.files:
            kubernetes_utils.utils.create_from_yaml(client, file)

    def destroy(client:KubernetesClientPlugin):
        """ Remove any resources created in apply """
        logger.warn('KubernetesSpecFilesWorkloadPlugin.destroy() not written yet')
