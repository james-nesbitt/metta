"""

Dummy client plugin

"""

import logging
from mirantis.testing.mtt.client import ClientBase

logger = logging.getLogger('mirantis.testing.mtt_dummy.client')

class DummyClientPlugin(ClientBase):
    """ Dummy client class

    As with all dummies, this is a failsafe plugin, that should never throw any
    exceptions if used according to mtt standards.

    It can be used as a placeholder during development, or it can be used to
    log client events and output for greater development and debugging.

    The client will log any method call, including unknown methods, and so it
    can be used in place of any client, if you don't need the methods to return
    anything
    """

    def args(self, *args, **kwargs):
        """ Client Interface: set client args """
        pass

    def __getattr__(self, name):
        """ Method call logger - log any called method """
        def method_log(*args):
            logger.info("dummy-client-exec [{}] : client.{}({})".format(self.instance_id, name, args))

        return method_log
