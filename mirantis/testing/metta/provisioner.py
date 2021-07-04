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


class ProvisionerBase:
    """Base Provisioner plugin class."""

    def prepare(self):
        """Prepare the provisioner to apply resources.

        Initial Provisioner plugin is expected to be of very low cost until
        prepare() is executed.  At this point the plugin should load any config
        and perform any validations needed.
        The plugin should not create any resources but it is understood that
        there may be a cost of preparation.

        Provisioners are expected to load a lot of config to self-program.
        Because of this, they allow passing of a configerus label for .load()
        and a base for .get() in case there is an alterante config source
        desired.

        """
        raise NotImplementedError("This provisioner has not yet implemented prepare")

    def apply(self):
        """Bring a cluster to the configured state."""
        raise NotImplementedError("This provisioner has not yet implemented apply")

    def destroy(self):
        """Remove all resources created for the cluster."""
        raise NotImplementedError("This provisioner has not yet implemented destroy")
