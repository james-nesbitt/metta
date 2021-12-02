"""

Metta k0sctl client plugin.

Metta plugin that gives configured access to k0sctl.

"""
from mirantis.testing.metta.environment import Environment

from .k0sctl import K0sctl

METTA_K0S_K0SCTL_CLIENT_PLUGIN_ID = ""
"""Metta plugin id for the k0scli client plugin."""


class K0sctlClientPlugin:
    """

    Metta client plugin for running configured k0scli commands.

    """

    def __init__(self, environment: Environment, instance_id: str):
        """Gather enough arguments to configure the SonobuoyClient object."""
        self._environment: Environment = environment
        """ Environemnt in which this plugin exists """
        self._instance_id: str = instance_id
        """ Unique id for this plugin instance """

        self.k0sctl: K0sctl = K0sctl()

    # the deep argument is a standard for the info hook
    # pylint: disable=unused-argument
    def info(self, deep: bool = False):
        """Return dict data about this plugin for introspection."""
        return {"k0sctl": self.k0sctl.info(deep=deep)}
