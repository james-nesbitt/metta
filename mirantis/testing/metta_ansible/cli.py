"""

Metta CLI : Ansible Provisioner commands.

Comamnds for itneracting with the ansible plugins, primarily the provisioner

"""
import logging

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.healthcheck import Health

from mirantis.testing.metta_cli.base import CliBase, cli_output

from .provisioner import METTA_ANSIBLE_PROVISIONER_PLUGIN_ID
from .ansible_callback import ResultsCallback

logger = logging.getLogger("metta.cli.ansible")

METTA_ANSIBLE_CLI_PLUGIN_ID = "metta_ansible_cli"
""" cli plugin_id for the info plugin """


# this interface is common for all Metta plugins, but CLI plugins underuse it
# pylint: disable=too-few-public-methods
class AnsibleCliPlugin(CliBase):
    """Fire command/group generator for Ansible commands."""

    def fire(self):
        """Return a dict of commands."""
        if (
            self._environment.fixtures.get(
                plugin_id=METTA_ANSIBLE_PROVISIONER_PLUGIN_ID,
                exception_if_missing=False,
            )
            is not None
        ):
            return {"contrib": {"ansible": AnsibleGroup(self._environment)}}

        return {}


class AnsibleGroup:
    """Base Fire command group for Ansible commands."""

    def __init__(self, environment: Environment):
        """Inject environment into command gorup."""
        self._environment = environment

    def _select_provisioner(self, instance_id: str = ""):
        """Pick a matching provisioner."""
        if instance_id:
            return self._environment.fixtures.get(
                plugin_id=[METTA_ANSIBLE_PROVISIONER_PLUGIN_ID],
                instance_id=instance_id,
            )

        # Get the highest priority provisioner
        return self._environment.fixtures.get(
            plugin_id=METTA_ANSIBLE_PROVISIONER_PLUGIN_ID,
        )

    def info(self, provisioner: str = "", deep: bool = False):
        """Get info about a provisioner plugin."""
        fixture = self._select_provisioner(instance_id=provisioner)
        return cli_output(fixture.info(deep=deep))

    def prepare(self, provisioner: str = ""):
        """Run provisioner prepare."""
        provisioner_plugin = self._select_provisioner(instance_id=provisioner).plugin
        provisioner_plugin.prepare()

    def apply(self, provisioner: str = ""):
        """Run provisioner apply."""
        provisioner_plugin = self._select_provisioner(instance_id=provisioner).plugin
        provisioner_plugin.apply()

    def destroy(self, provisioner: str = ""):
        """Run provisioner destroy."""
        provisioner_plugin = self._select_provisioner(instance_id=provisioner).plugin
        provisioner_plugin.destroy()

    # pylint: disable=protected-access
    def setup(self, provisioner: str = ""):
        """Run ansible plugin setup task."""
        provisioner_plugin = self._select_provisioner(instance_id=provisioner).plugin
        results: ResultsCallback = provisioner_plugin._ansible.setup()
        return cli_output(
            {
                str(result.host): {
                    "host": result.host,
                    "status": result.status,
                    "result": result.result,
                }
                for result in results
            }
        )

    # pylint: disable=protected-access
    def debug(self, provisioner: str = ""):
        """Run ansible plugin debug task."""
        provisioner_plugin = self._select_provisioner(instance_id=provisioner).plugin
        results: ResultsCallback = provisioner_plugin._ansible.debug()
        return cli_output(
            {
                str(result.host): {
                    "host": result.host,
                    "status": result.status,
                    "result": result.result,
                }
                for result in results
            }
        )

    # pylint: disable=protected-access
    def ping(self, provisioner: str = ""):
        """Run ansible plugin ping task."""
        provisioner_plugin = self._select_provisioner(instance_id=provisioner).plugin
        results: ResultsCallback = provisioner_plugin._ansible.ping()
        return cli_output(
            {
                str(result.host): {
                    "host": result.host,
                    "status": result.status,
                    "result": result.result,
                }
                for result in results
            }
        )

    def health(self, provisioner: str = ""):
        """Run provisioner destroy."""
        provisioner_fixture = self._select_provisioner(instance_id=provisioner)
        provisioner_plugin = provisioner_fixture.plugin
        health: Health = provisioner_plugin.health()
        return cli_output(
            {
                "fixture": {
                    "plugin_id": provisioner_fixture.plugin_id,
                    "instance_id": provisioner_fixture.instance_id,
                    "priority": provisioner_fixture.priority,
                },
                "status": health.status(),
                "messages": list(health._messages),
            }
        )
