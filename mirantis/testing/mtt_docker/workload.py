"""

Docker workload plugin

"""

class DockerWorkloadBase:
    """ Docker workload for docker runs """

    def __init__(self, conf, client):
        """ constructor """
        self.conf = conf
        self.client = client

class DockerRunWorkload(DockerWorkloadBase):
    """ Docker workload for docker runs """


class DockerStackWorkload(DockerWorkloadBase):
    """ Docker workload for docker-stacks """
