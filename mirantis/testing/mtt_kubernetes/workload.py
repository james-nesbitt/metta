"""

Kubernetes workload plugin

"""

def factory(conf):
    """ Kubernetes workload plugin factory (see mtt/plugin/factory) """
    return KubernetesWorkload(conf)

class KubernetesApplyWorkload:
    """ Kubernetes workload class """

    def __init__(self, conf):
        """ constructor """
        self.conf = conf
