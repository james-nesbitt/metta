"""

Metta CLI : Ansible Provisioner commands.

Comamnds for itneracting with the ansible plugins, primarily the provisioner

"""
import logging

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta_health.healthcheck import Health

from mirantis.testing.metta_cli.base import CliBase, cli_output

from .ansiblecli_provisioner import METTA_ANSIBLE_ANSIBLECLIPLAYBOOK_PROVISIONER_PLUGIN_ID
from .ansiblecli_client import (
    METTA_ANSIBLE_ANSIBLECLI_CORECLIENT_PLUGIN_ID,
    METTA_ANSIBLE_ANSIBLECLI_PLAYBOOKCLIENT_PLUGIN_ID,
)
from .ansiblecli_workload import (
    METTA_ANSIBLE_ANSIBLECLI_COREWORKLOAD_PLUGIN_ID,
    METTA_ANSIBLE_ANSIBLECLI_PLAYBOOKWORKLOAD_PLUGIN_ID,
)

logger = logging.getLogger("metta.cli.ansible")

METTA_ANSIBLE_CLI_PLUGIN_ID = "metta_ansible_cli"
""" cli plugin_id for the info plugin """


# this interface is common for all Metta plugins, but CLI plugins underuse it
# pylint: disable=too-few-public-methods
class AnsibleCliPlugin(CliBase):
    """Fire command/group generator for Ansible commands."""

    def fire(self):
        """Return a dict of commands."""
        commands = {}

        if (
            self._environment.fixtures().get(
                plugin_id=METTA_ANSIBLE_ANSIBLECLI_CORECLIENT_PLUGIN_ID,
                exception_if_missing=False,
            )
            is not None
        ):
            commands["ansible"] = AnsibleCliClientGroup(self._environment)

        if (
            self._environment.fixtures().get(
                plugin_id=METTA_ANSIBLE_ANSIBLECLI_PLAYBOOKCLIENT_PLUGIN_ID,
                exception_if_missing=False,
            )
            is not None
        ):
            commands["ansible-playbook"] = AnsibleCliPlaybookClientGroup(self._environment)

        return commands


class AnsibleCliClientGroup:
    """Commands for interacting with a metta ansible core client plugin."""

    def __init__(self, environment: Environment):
        """Inject environment into command gorup."""
        self._environment: Environment = environment

        if (
            self._environment.fixtures().get(
                plugin_id=METTA_ANSIBLE_ANSIBLECLI_COREWORKLOAD_PLUGIN_ID,
                exception_if_missing=False,
            )
            is not None
        ):
            self.workload = AnsibleCliWorkgroupGroup(self._environment)

    def _select_client(self, instance_id: str = ""):
        """Pick a matching client."""
        if instance_id:
            return self._environment.fixtures().get(
                plugin_id=[METTA_ANSIBLE_ANSIBLECLI_CORECLIENT_PLUGIN_ID],
                instance_id=instance_id,
            )

        # Get the highest priority provisioner
        return self._environment.fixtures().get(
            plugin_id=METTA_ANSIBLE_ANSIBLECLI_CORECLIENT_PLUGIN_ID,
        )

    def info(self, client: str = "", deep: bool = False):
        """Get info about a client plugin."""
        fixture = self._select_client(instance_id=client)
        return cli_output(fixture.info(deep=deep))

    def debug(self, client: str = "", hosts: str = "all"):
        """Run client plugin debug module."""
        fixture = self._select_client(instance_id=client)
        plugin = fixture.plugin
        return cli_output(plugin.debug(hosts=hosts))

    def setup(self, client: str = "", hosts: str = "all"):
        """Run client plugin setup module."""
        fixture = self._select_client(instance_id=client)
        plugin = fixture.plugin
        return cli_output(plugin.setup(hosts=hosts))

    def ping(self, client: str = "", hosts: str = "all"):
        """Run client plugin ping module."""
        fixture = self._select_client(instance_id=client)
        plugin = fixture.plugin
        return cli_output(plugin.ping(hosts=hosts))

    def health(self, client: str = ""):
        """Run client healthcheck."""
        fixture = self._select_client(instance_id=client)
        plugin = fixture.plugin
        health: Health = plugin.health()
        return cli_output(
            {
                "fixture": {
                    "plugin_id": fixture.plugin_id,
                    "instance_id": fixture.instance_id,
                    "priority": fixture.priority,
                },
                "status": health.status(),
                "messages": list(health.messages()),
            }
        )


class AnsibleCliPlaybookClientGroup:
    """Commands for interacting with a metta ansible playbook client plugin."""

    def __init__(self, environment: Environment):
        """Inject environment into command gorup."""
        self._environment: Environment = environment

        if (
            self._environment.fixtures().get(
                plugin_id=METTA_ANSIBLE_ANSIBLECLIPLAYBOOK_PROVISIONER_PLUGIN_ID,
                exception_if_missing=False,
            )
            is not None
        ):
            self.provisioner = AnsibleCliPlaybookProvisionerGroup(self._environment)

        if (
            self._environment.fixtures().get(
                plugin_id=METTA_ANSIBLE_ANSIBLECLI_PLAYBOOKWORKLOAD_PLUGIN_ID,
                exception_if_missing=False,
            )
            is not None
        ):
            self.workload = AnsibleCliPlaybookWorkgroupGroup(self._environment)

    def _select_client(self, instance_id: str = ""):
        """Pick a matching client."""
        if instance_id:
            return self._environment.fixtures().get(
                plugin_id=[METTA_ANSIBLE_ANSIBLECLI_CORECLIENT_PLUGIN_ID],
                instance_id=instance_id,
            )

        # Get the highest priority provisioner
        return self._environment.fixtures().get(
            plugin_id=METTA_ANSIBLE_ANSIBLECLI_CORECLIENT_PLUGIN_ID,
        )

    def info(self, client: str = "", deep: bool = False):
        """Get info about a client plugin."""
        fixture = self._select_client(instance_id=client)
        return cli_output(fixture.info(deep=deep))

    def run(self, playbook: str, client: str = ""):
        """Get info about a client plugin."""
        fixture = self._select_client(instance_id=client)
        plugin = fixture.plugin
        return cli_output(plugin.run_file(playbook))


class AnsibleCliPlaybookProvisionerGroup:
    """Commands for interacting with a metta ansible provisioner plugin."""

    def __init__(self, environment: Environment):
        """Inject environment into command gorup."""
        self._environment: Environment = environment

    def _select_provisioner(self, instance_id: str = ""):
        """Pick a matching provisioner."""
        if instance_id:
            return self._environment.fixtures().get(
                plugin_id=[METTA_ANSIBLE_ANSIBLECLIPLAYBOOK_PROVISIONER_PLUGIN_ID],
                instance_id=instance_id,
            )

        # Get the highest priority provisioner
        return self._environment.fixtures().get(
            plugin_id=METTA_ANSIBLE_ANSIBLECLIPLAYBOOK_PROVISIONER_PLUGIN_ID,
        )

    def info(self, provisioner: str = "", deep: bool = False):
        """Get info about a provisioner plugin."""
        fixture = self._select_provisioner(instance_id=provisioner)
        return cli_output(fixture.info(deep=deep))

    def prepare(self, provisioner: str = ""):
        """Run provisioner prepare."""
        provisioner_plugin = self._select_provisioner(instance_id=provisioner).plugin
        provisioner_plugin.prepare(self._environment.fixtures())

    def apply(self, provisioner: str = ""):
        """Run provisioner apply."""
        provisioner_plugin = self._select_provisioner(instance_id=provisioner).plugin
        provisioner_plugin.apply()

    def destroy(self, provisioner: str = ""):
        """Run provisioner destroy."""
        provisioner_plugin = self._select_provisioner(instance_id=provisioner).plugin
        provisioner_plugin.destroy()


class AnsibleCliWorkgroupGroup:
    """Commands for interacting with a metta ansible workgroup plugin."""

    def __init__(self, environment: Environment):
        """Inject environment into command gorup."""
        self._environment: Environment = environment

    def _select_workgroup(self, instance_id: str = ""):
        """Pick a matching workgroup."""
        if instance_id:
            return self._environment.fixtures().get(
                plugin_id=[METTA_ANSIBLE_ANSIBLECLI_CORECLIENT_PLUGIN_ID],
                instance_id=instance_id,
            )

        # Get the highest priority provisioner
        return self._environment.fixtures().get(
            plugin_id=METTA_ANSIBLE_ANSIBLECLI_CORECLIENT_PLUGIN_ID,
        )

    def info(self, workgroup: str = "", deep: bool = False):
        """Get info about the plugin."""
        fixture = self._select_workgroup(instance_id=workgroup)
        return cli_output(fixture.info(deep=deep))

    def apply(self, workgroup: str = ""):
        """Apply the plygin workload."""
        fixture = self._select_workgroup(instance_id=workgroup)
        plugin = fixture.plugin
        plugin.prepare(self._environment.fixtures())
        plugin.apply()


class AnsibleCliPlaybookWorkgroupGroup:
    """Commands for interacting with a metta ansible playbook workgroup plugin."""

    def __init__(self, environment: Environment):
        """Inject environment into command gorup."""
        self._environment: Environment = environment

    def _select_workgroup(self, instance_id: str = ""):
        """Pick a matching workgroup."""
        if instance_id:
            return self._environment.fixtures().get(
                plugin_id=[METTA_ANSIBLE_ANSIBLECLI_PLAYBOOKWORKLOAD_PLUGIN_ID],
                instance_id=instance_id,
            )

        # Get the highest priority provisioner
        return self._environment.fixtures().get(
            plugin_id=METTA_ANSIBLE_ANSIBLECLI_PLAYBOOKWORKLOAD_PLUGIN_ID,
        )

    def info(self, workgroup: str = "", deep: bool = False):
        """Get info about the plugin."""
        fixture = self._select_workgroup(instance_id=workgroup)
        fixture.plugin.prepare()
        return cli_output(fixture.info(deep=deep))

    def apply(self, workgroup: str = ""):
        """Apply the plugin workload."""
        fixture = self._select_workgroup(instance_id=workgroup)
        plugin = fixture.plugin
        plugin.prepare(self._environment.fixtures())
        plugin.apply()
