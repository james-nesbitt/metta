"""

Metta CLI : Fixture commands.

Cli plugin that allows examination of fixtures in environments.

"""

import logging
from typing import List

from mirantis.testing.metta.plugin import Factory
from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.fixture import Fixtures

from .base import CliBase, cli_output, METTA_PLUGIN_INTERFACE_ROLE_CLI

logger = logging.getLogger("metta.cli.fixtures")


# this interface is common for all Metta plugins, but CLI plugins underuse it
# pylint: disable=too-few-public-methods
class FixturesCliPlugin(CliBase):
    """Fire command/group generator for fixture commands."""

    def fire(self):
        """Return a dict of commands."""
        return {"fixture": FixturesGroup(self._environment)}


class FixturesGroup:
    """Base Fire command group for fixtures commands."""

    def __init__(self, environment: Environment):
        """Attach environment to object."""
        self._environment: Environment = environment

    # pylint: disable=too-many-arguments
    def _filter(
        self,
        plugin_id: str = "",
        instance_id: str = "",
        interfaces: List[str] = None,
        labels: List[str] = None,
        skip_cli_plugins: bool = True,
    ):
        """Filter fixtures centrally."""
        matches = self._environment.fixtures().filter(
            plugin_id=plugin_id, instance_id=instance_id, interfaces=interfaces, labels=labels
        )

        if not skip_cli_plugins:
            return matches

        # filter out cli plugins
        fixtures = Fixtures()
        for fixture in matches:
            if METTA_PLUGIN_INTERFACE_ROLE_CLI not in fixture.interfaces:
                fixtures.add(fixture)
        return fixtures

    # methods needs to be on object for cli registation
    # pylint: disable=no-self-use
    def plugins(
        self,
        interface: str = "",
        label: str = "",
        skip_cli_plugins: bool = True,
    ):
        """List registered plugins and interfaces."""
        plugins_info = {}

        # use a protected property just for introspection
        # pylint: disable=protected-access
        for registration in Factory._registry.values():
            if skip_cli_plugins and METTA_PLUGIN_INTERFACE_ROLE_CLI in registration.interfaces:
                continue

            if interface and interface not in registration.interfaces:
                continue
            if label and label not in registration.labels:
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
        interface: str = "",
        label: str = "",
        skip_cli_plugins: bool = True,
    ):
        """Return Info for fixtures."""
        fixture_info_list = []
        for fixture in self._filter(
            plugin_id=plugin_id,
            instance_id=instance_id,
            interfaces=[interface] if interface else [],
            labels=[label] if label else [],
            skip_cli_plugins=skip_cli_plugins,
        ):
            fixture_info_list.append(fixture.info(deep=deep, children=children))

        return cli_output(fixture_info_list)

    # this is what is needed to limit or filter fixture introspection
    # pylint: disable=too-many-arguments
    def list(
        self,
        plugin_id: str = "",
        instance_id: str = "",
        interface: str = "",
        label: str = "",
        skip_cli_plugins: bool = True,
    ):
        """Return Info for fixtures."""
        fixture_info_list = []
        for fixture in self._filter(
            plugin_id=plugin_id,
            instance_id=instance_id,
            interfaces=[interface] if interface else [],
            labels=[label] if label else [],
            skip_cli_plugins=skip_cli_plugins,
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
