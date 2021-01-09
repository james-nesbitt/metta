"""

Dummy MTT provisioner pluging

"""

class DummyProvisioner:
    """ Dummy provisioner class """

    def __init__(self, conf):
        """ constructor """
        self.conf = conf

    def up(self):
        """ pretend to bring a cluster up """
        pass

    def down(self):
        """ pretend to brind a cluster down """
