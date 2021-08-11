"""

PLUGIN: Provisioner.

Provisioning plugins meet a common interface standard for managing a testing
system, where the provisioning keywords relate to creating and tearing down the
system.

"""

import logging

logger = logging.getLogger("metta.provisioner")

METTA_PLUGIN_INTERFACE_ROLE_PROVISIONER = "provisioner"
""" metta plugin interface identifier for client plugins """

METTA_PROVISIONER_CONFIG_PROVISIONERS_LABEL = "provisioners"
""" A centralized configerus load labe for multiple provisioners """
METTA_PROVISIONER_CONFIG_PROVISIONER_LABEL = "provisioner"
""" A centralized configerus load label a provisioner """
METTA_PROVISIONER_CONFIG_PROVISIONERS_KEY = "provisioners"
""" A centralized configerus key for multiple provisioners """
METTA_PROVISIONER_CONFIG_PROVISIONER_KEY = "provisioner"
""" A centralized configerus key for one provisioner """
