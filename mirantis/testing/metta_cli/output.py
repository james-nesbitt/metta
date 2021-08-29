"""

Metta CLI : Output commands.

Various commands that allow introspection of output plugins/fixtures and
their contents.

"""
import logging
from typing import List


from mirantis.testing.metta.plugin import Factory
from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.output import METTA_PLUGIN_INTERFACE_ROLE_OUTPUT

from .base import CliBase, cli_output

logger = logging.getLogger("metta.cli.output")


# this interface is common for all Metta plugins, but CLI plugins underuse it
# pylint: disable=too-few-public-methods
class OutputCliPlugin(CliBase):
    """Fire command/group generator for output commands."""

    def fire(self):
        """Return a dict of commands."""
        return {"output": OutputGroup(self._environment)}


class OutputGroup:
    """Base Fire command group for output commands."""

    def __init__(self, environment: Environment):
        """Create CLI command group."""
        self._environment: Environment = environment

    # pylint: disable=too-many-arguments
    def _filter(
        self,
        plugin_id: str = "",
        instance_id: str = "",
        has_labels: List[str] = None,
    ):
        """Filter fixtures centrally."""
        return self._environment.fixtures().filter(
            plugin_id=plugin_id,
            instance_id=instance_id,
            has_labels=has_labels,
            interfaces=METTA_PLUGIN_INTERFACE_ROLE_OUTPUT,
        )

    # methods needs to be on object for cli registation
    # pylint: disable=no-self-use
    def plugins(
        self,
        has_label: str = "",
    ):
        """List registered plugins and interfaces."""
        plugins_info = {}

        # use a protected property just for introspection
        # pylint: disable=protected-access
        for registration in Factory._registry.values():
            if METTA_PLUGIN_INTERFACE_ROLE_OUTPUT not in registration.interfaces:
                continue
            if has_label and has_label not in registration.labels:
                continue

            plugins_info[registration.plugin_id] = {
                "plugin_id": registration.plugin_id,
                "interfaces": registration.interfaces,
                "labels_from_factory": registration.labels,
            }

        return cli_output(plugins_info)

    # this is what is needed to limit or filter fixture introspection
    # pylint: disable=too-many-arguments
    def info(
        self,
        deep: bool = False,
        children: bool = False,
        plugin_id: str = "",
        instance_id: str = "",
        has_label: str = "",
    ):
        """Return Info for fixtures."""
        fixture_info_list = []
        for fixture in self._filter(
            plugin_id=plugin_id,
            instance_id=instance_id,
            has_labels=[has_label] if has_label else [],
        ):
            fixture_info_list.append(fixture.info(deep=deep, children=children))

        return cli_output(fixture_info_list)

    # this is what is needed to limit or filter fixture introspection
    # pylint: disable=too-many-arguments
    def list(
        self,
        plugin_id: str = "",
        instance_id: str = "",
        has_label: str = "",
    ):
        """Return Info for fixtures."""
        fixture_info_list = []
        for fixture in self._filter(
            plugin_id=plugin_id,
            instance_id=instance_id,
            has_labels=[has_label] if has_label else [],
        ):
            fixture_info_list.append(
                {
                    "plugin_id": fixture.plugin_id,
                    "instance_id": fixture.instance_id,
                    "interfaces": fixture.interfaces,
                    "labels": fixture.labels,
                }
            )

        return cli_output(fixture_info_list)
