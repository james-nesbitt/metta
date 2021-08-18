"""

Metta client plugin for testkit.

"""

import logging
from typing import Any, Dict, List

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.fixture import Fixtures

from mirantis.testing.metta_mirantis.mke_client import (
    MKEAPIClientPlugin,
    METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID,
)
from mirantis.testing.metta_mirantis.msr_client import METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID

from .testkit import TestkitClient

logger = logging.getLogger("testkit.client")

METTA_TESTKIT_CLIENT_PLUGIN_ID = "metta_testkit_client"
""" Metta plugin id for testkit provisioner plugins """


class TestkitClientPlugin:
    """Testkit client plugin.

    client plugin that allows control of and interaction with a testkit
    cluster.

    ## Requirements

    1. this plugin uses subprocess to call a testkit binary, so you have to
       install testkit in the environment

    ## Usage

    @TODO

    """

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        environment,
        instance_id,
        system_name: str,
        config_file: str,
        systems: Dict[str, Dict[str, str]] = None,
    ):
        """Initialize Testkit provisioner.

        Parameters:
        -----------
        environment (Environment) : metta environment object that this plugin
            is attached.
        instance_id (str) : label for this plugin instances.
        config_file (str) : string path to the testkit config file.
        systems (Dict[str, Dict[str, str]]) : A dictionary of systems which this
            client is expected to provide using testkit.

            This is something which should be determinable using the config/file
            client directly, but sits outside of information encapsulated in
            the tool/conf.

            What we are talking about here is information to answer questions:

                Did testkit install MKE? if so, what accesspoint and U/P can I
                use to build an MKE client to access it.

            This is not an ideal approach but rather a necessity.

        """
        self._environment: Environment = environment
        """ Environemnt in which this plugin exists """
        self._instance_id: str = instance_id
        """ Unique id for this plugin instance """

        self._system_name: str = system_name
        """ What will testkit call the system, used client ops """

        self._testkit = TestkitClient(config_file=config_file)
        """ testkit client object """

        self._systems = systems
        """What systems will testkit install, so what fixtures are needed"""

        self.fixtures = Fixtures()
        """This object makes and keeps track of fixtures for MKE/MSR clients."""
        try:
            self.make_fixtures()
            # pylint: disable= broad-except
        except Exception as err:
            # there are many reasons this can fail, and we just want to
            # see if we can get fixtures early.
            # No need to ask forgiveness for this one.
            logger.debug("Could not make initial fixtures: %s", err)

    # the deep argument is a standard for the info hook
    # pylint: disable=unused-argument
    def info(self, deep: bool = False) -> Dict[str, Any]:
        """Get info about a provisioner plugin."""
        info = {
            "plugin": {
                "system_name": self._system_name,
            },
            "client": self._testkit.info(deep=deep),
        }
        if deep:
            try:
                info["hosts"] = self.hosts()
            # pylint: disable=broad-except
            except Exception:
                pass

        return info

    def version(self):
        """Return testkit client version."""
        return self._testkit.version()

    def create(self, opts: List[str]):
        """Run the testkit create command."""
        self._testkit.create(opts=opts)
        self.make_fixtures()

        mke_plugin = self._get_mke_client_plugin()
        mke_plugin.api_get_bundle(force=True)
        mke_plugin.make_fixtures()

    def destroy(self):
        """Remove a system from testkit."""
        return self._testkit.system_rm(system_name=self._system_name)

    def hosts(self):
        """List testkit system machines."""
        return self._testkit.machine_ls(system_name=self._system_name)

    def exec(self, host: str, cmd: str):
        """List testkit system machines."""
        return self._testkit.machine_ssh(machine=host, cmd=cmd)

    def system_ls(self):
        """List all of the systems testkit can see using our config."""
        return self._testkit.system_ls()

    # pylint: disable=too-many-branches
    def make_fixtures(self):
        """Make related fixtures from a testkit installation.

        Creates:
        --------

        MKE client : if we have manager nodes, then we create an MKE client
            which will then create docker and kubernestes clients if they are
            appropriate.

        MSR Client : if we have an MSR node, then the related client is
            created.

        """
        if self._systems is None:
            return

        testkit_hosts = self._testkit.machine_ls(system_name=self._system_name)
        """ list of all of the testkit hosts. """

        manager_hosts = []
        worker_hosts = []
        mke_hosts = []
        msr_hosts = []
        for host in testkit_hosts:
            host["address"] = host["public_ip"]
            if host["swarm_manager"] == "yes":
                manager_hosts.append(host)
            else:
                worker_hosts.append(host)

            if host["ucp_controller"] == "yes":
                mke_hosts.append(host)

        if len(msr_hosts) == 0 and len(worker_hosts) > 0:
            # Testkit installs MSR on the first work node, but the api is
            # accessible using port 444 in order to not conflict.
            first_worker = worker_hosts[0]
            first_worker_ip = first_worker["public_ip"]
            first_worker["msr_accesspoint"] = f"{first_worker_ip}:444"
            msr_hosts.append(first_worker)

        if len(mke_hosts) > 0 and METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID in self._systems:
            instance_id = f"{self._instance_id}-{METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID}"
            arguments = self._systems[METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID]
            arguments["hosts"] = mke_hosts

            if "accesspoint" in arguments and arguments["accesspoint"]:
                arguments["accesspoint"] = clean_accesspoint(arguments["accesspoint"])

            logger.debug("Launchpad client is creating an MKE client plugin: %s", instance_id)
            fixture = self._environment.new_fixture(
                plugin_id=METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID,
                instance_id=instance_id,
                priority=70,
                arguments=arguments,
                labels={
                    "parent_plugin_id": METTA_TESTKIT_CLIENT_PLUGIN_ID,
                    "parent_instance_id": self._instance_id,
                },
                replace_existing=True,
            )
            self.fixtures.add(fixture, replace_existing=True)

            # We got an MKE client, so let's activate it.

        else:
            logger.debug("No MKE master hosts found, not creating an MKE client.")

        if len(msr_hosts) > 0 and METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID in self._systems:
            instance_id = f"{self._instance_id}-{METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID}"
            arguments = self._systems[METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID]
            arguments["hosts"] = msr_hosts

            if "accesspoint" in arguments and arguments["accesspoint"]:
                arguments["accesspoint"] = clean_accesspoint(arguments["accesspoint"])

            logger.debug("Launchpad client is creating an MSR client plugin: %s", instance_id)
            fixture = self._environment.new_fixture(
                plugin_id=METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID,
                instance_id=instance_id,
                priority=70,
                arguments=arguments,
                labels={
                    "parent_plugin_id": METTA_TESTKIT_CLIENT_PLUGIN_ID,
                    "parent_instance_id": self._instance_id,
                },
                replace_existing=True,
            )
            self.fixtures.add(fixture, replace_existing=True)

        else:
            logger.debug("No MSR master hosts found, not creating an MSR client.")

    def _get_mke_client_plugin(self) -> MKEAPIClientPlugin:
        """Retrieve the MKE client plugin if we can."""
        try:
            return self.fixtures.get_plugin(plugin_id=METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID)
        except KeyError as err:
            raise RuntimeError(
                "Launchpad client cannot find its MKE client plugin, and "
                "cannot process any client actions.  Was a client created?"
            ) from err


def clean_accesspoint(accesspoint: str) -> str:
    """Remove any https:// and end / from an accesspoint."""
    accesspoint = accesspoint.replace("https://", "")
    return accesspoint
