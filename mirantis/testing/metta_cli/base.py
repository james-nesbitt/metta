"""

CLI Plugins base.

@TODO move to the metta_cli package

Define a base class and some constants for the CLI plugins.  The CLI plugins
provide functionality for the metta cli tool, which is provided by the
metta_cli package.  This is here because the plugin types are defined as an
enum in this package, and so the base class is here too.

"""
import logging
import json
from typing import Any

from mirantis.testing.metta.environment import Environment

logger = logging.getLogger("metta.cli.base")

METTA_PLUGIN_INTERFACE_ROLE_CLI = "cli"
""" Metta plugin interface identifier for CLI plugins """


# pylint: disable=too-few-public-methods
class CliBase:
    """Base class/interface for cli plugins.

    Mainly here as an interface definition so that you know what you have to
    add to get it to work with the metta_cli system.

    """

    def __init__(self, environment: Environment, instance_id: str):
        """Inject Environment and instance_id into plugin."""
        self._environment: Environment = environment
        """ Environemnt in which this plugin exists """
        self._instance_id: str = instance_id
        """ Unique id for this plugin instance """

    def fire(self):
        """Execute the fire cli hook."""
        raise NotImplementedError("this functionality not available.")


def cli_output(structure: Any) -> str:
    """Format data for output from cli commands.

    Parameters:
    -----------
    structure (Any) : data to be formatted for cli return

    Returns:
    --------
    String conversion, as json

    """
    return json.dumps(structure, indent=2, default=_serialize_last_resort)


def _serialize_last_resort(target: Any) -> str:
    """Serialzie anything.

    Returns:
    --------
    This target as a string.  Serialized for output only.

    """
    return f"{target}"
