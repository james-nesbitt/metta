import logging

from configerus.config import Config

from .plugin import METTAPlugin, Type

logger = logging.getLogger('metta.client')

METTA_PLUGIN_TYPE_CLIENT = Type.CLIENT
""" Fast access to the client plugin_id """

METTA_CLIENT_CONFIG_CLIENTS_LABEL = 'clients'
""" A centralized configerus label for multiple clients """
METTA_CLIENT_CONFIG_CLIENT_LABEL = 'client'
""" A centralized configerus label for a client """
METTA_CLIENT_CONFIG_CLIENTS_KEY = 'clients'
""" A centralized configerus key for multiple clients """
METTA_CLIENT_CONFIG_CLIENT_KEY = 'client'
""" A centralized configerus key for one client """


class ClientBase(METTAPlugin):
    """ Base class for client plugins """
    pass
