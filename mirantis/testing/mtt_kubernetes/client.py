"""

Kubernetes client plugin

"""

import logging
import kubernetes

logger = logging.getLogger("mirantis.testing.mtt_kubernetes.client")

class KubernetesClient:
    """ Kubernetes client class """

    def __init__(self, conf, config_file: str, context=None):
        """ constructor """
        self.conf = conf
        self.api_client = kubernetes.config.new_client_from_config(config_file=config_file)

    def get_CoreV1Api_client(self):
        """ Get a CoreV1Api client """
        return kubernetes.client.CoreV1Api(self.api_client)

# /home/james/.mirantis-launchpad/cluster/launchpad-mke/bundle/admin/kube.yml
