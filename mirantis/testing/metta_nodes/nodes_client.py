"""

A Metta client plugin for interacting with a set of host nodes.

This plugin is meant to provide various access methods to a list of hosts that
are meant to act as nodes in a cluster.
"""

import logging
from typing import Dict, Any, List

from configerus.contrib.jsonschema.validate import (
    PLUGIN_ID_VALIDATE_JSONSCHEMA_SCHEMA_CONFIG_LABEL,
)
from configerus.validator import ValidationError

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta_health.healthcheck import Health

logger = logging.getLogger("metta_common.nodes")

METTA_PLUGIN_ID_NODES_CLIENT = "metta_common_nodes_client"
""" client plugin_id for the metta nodes list client plugin """


METTA_NODES_CONFIG_LABEL = "launchpad"
""" Launchpad config label for configuration """
METTA_NODES_CLIENT_SYSTEMS_KEY = "systems"
""" If provided, this config key provide a dictionary of configuration of client system plugins. """
METTA_NODES_CONFIG_ROOT_PATH_KEY = "root.path"
""" config key for a base file path that should be used for any relative paths """
METTA_NODES_CONFIG_KEY = "config"
""" which config key will provide the launchpad yml """
METTA_NODES_CLI_CONFIG_FILE_KEY = "config_file"
""" Launchpad config cli key to tell us where to put the launchpad yml file """
METTA_NODES_CLI_WORKING_DIR_KEY = "working_dir"
""" Launchpad config cli configuration working dir key """
METTA_NODES_CLI_CLUSTEROVERRIDE_KEY = "cluster_name"
""" If provided, this config key will override a cluster name pulled from yaml"""
METTA_NODES_CLI_OPTIONS_KEY = "cli"
""" If provided, these will be passed to the launchpad client to be used on all operations"""

METTA_NODES_VALIDATE_JSONSCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "additionalProperties": False,
        "oneOf": [
            {
                # A node with SSH capabilities
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "id": {"type": "string"},
                    "role": {"type": "string"},
                    "ssh": {
                        "type": "object",
                        "properties": {
                            "address": {"type": "string"},
                            "keyPath": {"type": "string"},
                            "user": {"type": "string"},
                        },
                        "required": ["address", "keyPath", "user"],
                    },
                },
                "required": ["id"],
            },
        ],
    },
}
""" Validation jsonschema for list of hosts """
METTA_NODES_PROVISIONER_VALIDATE_TARGET = {
    PLUGIN_ID_VALIDATE_JSONSCHEMA_SCHEMA_CONFIG_LABEL: METTA_NODES_VALIDATE_JSONSCHEMA
}
"""Configerus validation target to validate config as a set of hosts."""


class NodesClientPlugin:
    """Metta Client plugin for interacting with a set of host nodes."""

    def __init__(self, environment: Environment, instance_id: str, nodes: List[Dict[str, Any]]):
        """Associate a List of nodes with the client

        Parameters:
        -----------
        hosts (List[Dict[str, Any]]) : this list of nodes.
            This is hard to nail down as the feature set is option and Still
            growing.

            We know that the node must have the following:

            id (str) : unique identifer for the node, used to select which node
                to operate on when using the client.

            We know that it can have:

            ssh (Dict[str, str]) :
                address (str) : reachable ssh address
                keyPath (str) : path to an ssh key
                user (str) : username to be used for ssh

        """
        self._environment = environment
        """ Environemnt in which this plugin exists """
        self._instance_id = instance_id
        """ Unique id for this plugin instance """

        self._nodes: Dict[str, HostNode] = {}
        """Dictionary of node objects."""

        self.set_nodes(nodes)

    def info(self, deep: bool = False) -> Dict[str, Any]:
        """Return structured information for introspection."""
        return {"nodes": {node: self._nodes[node].info(deep=deep) for node in self._nodes}}

    def health(self) -> Health:
        """Report client health as an aggregate of node health."""
        agg_health = Health(source=self._instance_id)
        for node in self._nodes:
            agg_health.merge(node.health())
        return agg_health

    def set_nodes(self, nodes: List[Dict[str, Any]]):
        """Assign a set of nodes to the client.

        This unsets any nodes previously assigned.
        """
        try:
            self._environment.config.validate(
                data=nodes, validate_target=METTA_NODES_PROVISIONER_VALIDATE_TARGET
            )
        except ValidationError as err:
            raise RuntimeError("Nodes client received invalid node list") from err

        self._nodes: Dict[str, HostNode] = {
            node: HostNode(self._instance_id, nodes[node]) for node in nodes.keys()
        }
