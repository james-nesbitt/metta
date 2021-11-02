"""

Metta client plugin for launchpad.

Primarily a metta plugin interface for the ./launchpad subprocess client, but in a form
that acts as a metta plugin.  This means that it can form a part of an metta environment.

Most other plugins that use launchpad will themselves proxy to this plugin.

"""
import logging
from typing import Dict, Any, List
import subprocess

from configerus.loaded import Loaded

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.fixture import Fixtures

from mirantis.testing.metta_mirantis.mke_client import (
    MKEAPIClientPlugin,
    METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID,
)
from mirantis.testing.metta_mirantis.msr_client import METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID

from .launchpad import (
    LaunchpadClient,
    METTA_LAUNCHPAD_CLI_CONFIG_FILE_DEFAULT,
    METTA_LAUNCHPADCLIENT_WORKING_DIR_DEFAULT,
)

logger = logging.getLogger("metta_launchpad:provisioner")

METTA_LAUNCHPAD_CLIENT_PLUGIN_ID = "metta_launchpad_client"
""" Metta plugin_id for the launchpad provisioner plugin """

METTA_LAUNCHPAD_CONFIG_HOSTS_KEY = "spec.hosts"
""" config key for the list of cluster hosts. """
METTA_LAUNCHPAD_CONFIG_HOST_ROLE_KEY = "role"
""" config key for the role of a host """

METTA_LAUNCHPAD_CLI_CONFIG_DOCKER_VERSION_DEFAULT = "1.40"
""" Default value for the docker client version number."""


# pylint: disable=too-many-arguments
class LaunchpadClientPlugin:
    """Metta client plugin for launchpad."""

    def __init__(
        self,
        environment: Environment,
        instance_id: str,
        config_file: str = METTA_LAUNCHPAD_CLI_CONFIG_FILE_DEFAULT,
        working_dir: str = METTA_LAUNCHPADCLIENT_WORKING_DIR_DEFAULT,
        cli_options: Dict[str, bool] = None,
        systems: Dict[str, Dict[str, str]] = None,
    ):
        """Collect enough data to create a LaunchpadClient object.

        Parameters:
        -----------
        config_file (str) : Path to the launchpad yml config file.

        working_dir (str) : Path CWD to use for subprocess with launchpad.  This may be needed
            if PEMs in the yaml are relative paths.

        cli_options (Dict[str, Any]) : Additional -- flags which should be passed to all
            launchpad commands.

        systems (Dict[str, Any]) : Dictionary to provide client generation for infrastructure
            created by Launchpad.  The two primary examples are MKE and MSR.

            Each key of the Dict is the identifier of the system, and its values are arguments
            to the constructor of the system, except the host list.

            An example for MKE:
                "mke": {
                    "accesspoint": "192.168.172.11",
                    "username": "admin"",
                    "password": "orca",
                }

                A host list will be added to the arguments.

        """
        self._environment: Environment = environment
        """ Environemnt in which this plugin exists """
        self._instance_id: str = instance_id
        """ Unique id for this plugin instance """

        self.config_file: str = config_file
        """Path to the launchpad yml file."""

        self.systems: Dict[str, Dict[str, str]] = systems if systems is not None else {}
        """Access endpoint & U/P for systems created by launchpad, such as the MKE client."""

        self._fixtures: Fixtures = Fixtures()
        """This plugin makes fixtures, and keeps track of them here."""

        logger.debug("Creating Launchpad client handler")
        self.launchpad: LaunchpadClient = LaunchpadClient(
            config_file=config_file,
            working_dir=working_dir,
            cli_options=cli_options,
        )

        # If we can, it makes sense to build the MKE and MSR client fixtures now.
        # This will only be possible in cases where we have an installed cluster.
        # We try that here, even though it is verbose and ugly, so that we have
        # the clients available for introspection, for all consumers.
        # We probably shouldn't, but it allows some flexibility.
        # attempt to be declarative and make the client plugin in case the
        # terraform chart has already been run.
        # self.make_fixtures()
        try:
            self.make_fixtures()

        # dont' block the construction on an exception
        # pylint: disable=broad-except
        except Exception:
            pass

    def info(self, deep: bool = False) -> Dict[str, Any]:
        """Get info about a provisioner plugin.

        Returns:
        --------
        Dict of introspective information about this plugin_info

        """
        return {
            "config": {
                "launchpad_yml_path": self.config_file,
            },
            "systems": self.systems,
            "client": self.launchpad.info(deep=deep),
        }

    def fixtures(self) -> Fixtures:
        """Return children fixtures of the client."""
        return self._fixtures

    def version(self):
        """Get the launchpad version."""
        return self.launchpad.version()

    def hosts(self, deep: bool = False):
        """List the hosts in the cluster."""
        config = self.describe_config()

        if deep:
            host_list = config["spec"]["hosts"]
        else:
            host_list = []
            for host in config["spec"]["hosts"]:
                list_host = {"role": host["role"]}
                if "ssh" in host:
                    list_host.update({"is_windows": False, "address": host["ssh"]["address"]})
                if "winrm" in host:
                    list_host.update({"is_windows": True, "address": host["winrm"]["address"]})

                host_list.append(list_host)

        return host_list

    def apply(self, debug: bool = False):
        """Bring a cluster up.

        We assume that the cluster is running and the we can pull the required
        yaml from an output fixture in the environment.

        This plugin needs an output fixture, probably of dict type.  It will
        Pull that structure for the launchpad yaml config file and dump it into
        its config path.
        The provisioner can find an output directly from the environment, or
        from a specific fixture source.  If you want the output to come from
        only a specific backend fixture then make sure that a "backend" config
        exists, otherwise just use an "output" config.

        Raises:
        -------
        ValueError if the object has been configured (prepare) with config that
            doesn't work, or if the backend doesn't give valid yml

        Exception if launchpad fails.

        """
        logger.info("Using launchpad to install products onto backend cluster")
        self.launchpad.apply(debug=debug)
        self.make_fixtures()

        try:
            mke_plugin = self._get_mke_client_plugin()
            # We got an MKE client, so let's activate it.
            mke_plugin.api_get_bundle(force=True)
            mke_plugin.make_fixtures()
        except KeyError as err:
            raise RuntimeError("Launchpad MKE client failed to download client bundle.") from err

        # as we have likely changed our cluster, tell everybody to download new
        # client bundles.
        try:
            # this plugin client maintains a client bundle
            self.launchpad.get_bundle(user="admin")
        except KeyError as err:
            raise RuntimeError("Launchpad client failed to download client bundle.") from err

    def reset(self):
        """Ask the client to remove installed resources."""
        # tell the MKE client to remove its bundles
        try:
            mke = self._fixtures.get_plugin(
                plugin_id=METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID,
            )
            mke.rm_bundle()

        except KeyError as err:
            logger.warning("Launchpad's MKE plugin failed do remove a client bundle: %s", err)

        # now tell the launchpad client to reset
        try:
            self.launchpad.reset()
            self.launchpad.rm_client_bundles()

        except subprocess.CalledProcessError as err:
            logger.warning("Launchpad failed to destroy installed resources: %s", err)

    def bundle(self, user: str = "admin", reload: bool = False) -> Dict[str, Any]:
        """Retrieve the user bundle for the marked user and return an info dict about it."""
        self.launchpad.get_bundle(user=user, reload=reload)
        return self.launchpad.bundle(user=user)

    def register(self, name: str, email: str, company: str):
        """Uninstall using the launchpad client."""
        return self.launchpad.register(name=name, email=email, company=company)

    def describe(self, report: str):
        """Output one of the launchpad reports."""
        return self.launchpad.describe(report=report)

    def describe_config(self) -> Dict[str, Any]:
        """Return the launchpad config report as interpreted by launchpad."""
        return self.launchpad.describe_config()

    def exec(self, host_index: int, cmds: List[str]):
        """Execute a command on a host index."""
        return self.launchpad.exec(host_index=host_index, cmds=cmds)

    def make_fixtures(self) -> Fixtures:
        """Build fixtures for all of the clients.

        Returns:
        --------
        Fixtures collection of fixtures that have been created

        """
        # get fresh values for the launchpad config (in case it has changed) and
        # treat this as a configerus Loaded object which allows us to use the
        # searching and validation syntax.
        client_config = self.describe_config()
        launchpad_config = Loaded(data=client_config, parent=None, instance_id="launchpad_client")

        # Retrieve a list of hosts, and use that to decide what clients to
        # make.  If we find a host for a client, then we retrieve needed
        # config and use it to generate the related client.
        hosts = launchpad_config.get(METTA_LAUNCHPAD_CONFIG_HOSTS_KEY, default=[], format=False)

        # MKE Client
        #
        if METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID in self.systems:
            mke_hosts: List[Any] = list(
                host for host in hosts if host[METTA_LAUNCHPAD_CONFIG_HOST_ROLE_KEY] in ["manager"]
            )
            if len(mke_hosts) > 0:
                instance_id = f"{self._instance_id}-{METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID}"
                mke_arguments: Dict[str, Any] = self.systems[METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID]
                mke_arguments["hosts"] = mke_hosts

                if "accesspoint" in mke_arguments and mke_arguments["accesspoint"]:
                    mke_arguments["accesspoint"] = clean_accesspoint(mke_arguments["accesspoint"])

                logger.debug("Launchpad client is creating an MKE client plugin: %s", instance_id)
                fixture = self._environment.new_fixture(
                    plugin_id=METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID,
                    instance_id=instance_id,
                    priority=70,
                    arguments=mke_arguments,
                    labels={
                        "parent_plugin_id": METTA_LAUNCHPAD_CLIENT_PLUGIN_ID,
                        "parent_instance_id": self._instance_id,
                    },
                    replace_existing=True,
                )
                self._fixtures.add(fixture, replace_existing=True)

        # MSR Client
        #
        if METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID in self.systems:
            msr_hosts: List[Any] = list(
                host for host in hosts if host[METTA_LAUNCHPAD_CONFIG_HOST_ROLE_KEY] in ["msr"]
            )
            if len(msr_hosts) > 0:
                instance_id = f"{self._instance_id}-{METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID}"
                msr_arguments: Dict[str, Any] = self.systems[METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID]
                msr_arguments["hosts"] = msr_hosts

                if "accesspoint" in msr_arguments and msr_arguments["accesspoint"]:
                    msr_arguments["accesspoint"] = clean_accesspoint(msr_arguments["accesspoint"])

                logger.debug("Launchpad client is creating an MSR client plugin: %s", instance_id)
                fixture = self._environment.new_fixture(
                    plugin_id=METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID,
                    instance_id=instance_id,
                    priority=70,
                    arguments=msr_arguments,
                    labels={
                        "parent_plugin_id": METTA_LAUNCHPAD_CLIENT_PLUGIN_ID,
                        "parent_instance_id": self._instance_id,
                    },
                    replace_existing=True,
                )
                self._fixtures.add(fixture, replace_existing=True)

    def _get_mke_client_plugin(self) -> MKEAPIClientPlugin:
        """Retrieve the MKE client plugin if we can."""
        try:
            return self._fixtures.get_plugin(plugin_id=METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID)
        except KeyError as err:
            raise RuntimeError(
                "Launchpad client cannot find its MKE client plugin, and "
                "cannot process any client actions.  Was a client created?"
            ) from err


def clean_accesspoint(accesspoint: str) -> str:
    """Remove any https:// and end / from an accesspoint."""
    accesspoint = accesspoint.replace("https://", "")
    return accesspoint
