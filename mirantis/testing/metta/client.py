"""

PLUGIN: Client plugins.

Base definition for client type plugins.  This is not very "pythonish" but it
gives us a chance to define a base class and some constants related to that
kind of plugin.

"""

import logging

logger = logging.getLogger('metta.client')

METTA_PLUGIN_TYPE_CLIENT = 'client'
""" metta plugin type idnetifier for client plugins """

METTA_CLIENT_CONFIG_CLIENTS_LABEL = 'clients'
""" A centralized configerus label for multiple clients """
METTA_CLIENT_CONFIG_CLIENT_LABEL = 'client'
""" A centralized configerus label for a client """
METTA_CLIENT_CONFIG_CLIENTS_KEY = 'clients'
""" A centralized configerus key for multiple clients """
METTA_CLIENT_CONFIG_CLIENT_KEY = 'client'
""" A centralized configerus key for one client """
