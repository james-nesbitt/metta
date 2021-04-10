import json

from mirantis.testing.metta.plugin import Factory, Type
from mirantis.testing.metta.client import ClientBase
from mirantis.testing.metta.environment import Environment

# Register the plugin with metta


@Factory(type=Type.CLIENT, plugin_id="my_client")
def my_client_plugin_factory(
        environment: Environment, instance_id: str, label: str = 'my_client', base: str = ''):
    """ Build a custom client plugin which returns a custom output """
    return MyMessageClientPlugin(environment, instance_id, label, base)


class MyMessageClientPlugin(ClientBase):
    """ A custom client plugin

    This client plugin will return a different message from a configured list
    of messages until it has run out of messages.

    """

    def __init__(self, environment, instance_id, label, base):
        """

        Parameters:
        -----------

        All plugins receive these two:

        environment (Environment): Environment object which contains the plugin
        instance_id (str) : unique plugin instance identifier

        It is very common for plugins to configure themselved from config; which
        means that they should receive a config label and base key as arguments.

        label (str) : String configuerus load label for config
        base (str) : configuruse .get() key that should contain all of the config
            that this plugin needs.

        """

        self.messages = environment.config.load(label).get(
            [base, 'messages'])
        """ keep a list of string messages which we will serve one at a time """

    def __len__(self):
        """ How many messages are left """
        return len(self.messages)

    def get_message(self):
        """ Build and output fixture based on the next selection from the config """
        return self.messages.pop(0)

    def info(self):
        """ return structured information about the plugin for introspection """
        return {
            'messages': self.messages,
            'length': len(self)
        }
