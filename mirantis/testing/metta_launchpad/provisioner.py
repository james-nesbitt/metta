"""

Launchpad metta provisioner plugin.

Provisioner/Install  Mirantis products onto an existing cluster using
Launchpad.

"""
import os.path
import logging
from typing import Any, List, Dict
import subprocess
import yaml

from configerus.loaded import LOADED_KEY_ROOT
from configerus.contrib.jsonschema.validate import (
    PLUGIN_ID_VALIDATE_JSONSCHEMA_SCHEMA_CONFIG_LABEL,
)
from configerus.validator import ValidationError

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.fixtures import Fixtures
from mirantis.testing.metta.provisioner import ProvisionerBase
from mirantis.testing.metta_mirantis import (
    METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID,
    METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID,
)

from .launchpad import LaunchpadClient, METTA_LAUNCHPAD_CLI_CONFIG_FILE_DEFAULT
from .exec_client import METTA_LAUNCHPAD_EXEC_CLIENT_PLUGIN_ID

logger = logging.getLogger("mirantis.testing.metta.provisioner:launchpad")

METTA_LAUNCHPAD_PROVISIONER_PLUGIN_ID = "metta_launchpad_provisioner"
""" Metta plugin_id for the launchpad provisioner plugin """

METTA_LAUNCHPAD_CONFIG_LABEL = "launchpad"
""" Launchpad config label for configuration """
METTA_LAUNCHPAD_CONFIG_ROOT_PATH_KEY = "root.path"
""" config key for a base file path that should be used for any relative paths """
METTA_LAUNCHPAD_CONFIG_KEY = "config"
""" which config key will provide the launchpad yml """
METTA_LAUNCHPAD_CONFIG_MKE_ACCESSPOINT_KEY = "mke.accesspoint"
""" config key for the MKE endpoint, usually the manager load-balancer """
METTA_LAUNCHPAD_CONFIG_MKE_USERNAME_KEY = "mke.username"
""" config key for the MKE username """
METTA_LAUNCHPAD_CONFIG_MKE_PASSWORD_KEY = "mke.password"
""" config key for the MKE password """
METTA_LAUNCHPAD_CONFIG_MKE_CLIENTBUNDLE_KEY = "mke.client_bundle_root"
""" Config key for the MKE client bundle root path """
METTA_LAUNCHPAD_CONFIG_MSR_ACCESSPOINT_KEY = "msr.accesspoint"
""" config key for the MSR endpoint, usually the manager load-balancer """
METTA_LAUNCHPAD_CONFIG_MSR_USERNAME_KEY = "msr.username"
""" config key for the MSR username """
METTA_LAUNCHPAD_CONFIG_MSR_PASSWORD_KEY = "msr.password"
""" config key for the MSR password """
METTA_LAUNCHPAD_CONFIG_HOSTS_KEY = "config.spec.hosts"
""" config key for the list of hosts as per the launchpad spec """
METTA_LAUNCHPAD_CLI_CONFIG_FILE_KEY = "config_file"
""" Launchpad config cli key to tell us where to put the launchpad yml file """
METTA_LAUNCHPAD_CLI_WORKING_DIR_KEY = "working_dir"
""" Launchpad config cli configuration working dir key """
METTA_LAUNCHPAD_CLI_CLUSTEROVERRIDE_KEY = "cluster_name"
""" If provided, this config key will override a cluster name pulled from yaml"""
METTA_LAUNCHPAD_CLI_ACCEPTLICENSE_KEY = "cli.accept-license"
""" If provided, this config key will tell the cli to accept the license"""
METTA_LAUNCHPAD_CLI_DISABLETELEMETRY_KEY = "cli.disable-telemetry"
""" If provided, this config key will tell the cli to disable telemetry"""
METTA_LAUNCHPAD_CLI_DISABLETELEMETRYUPGRADECHECK_KEY = "cli.disable-upgrade-check"
""" If provided, this config key will tell the cli to disable upgrade checks"""
METTA_LAUNCHPAD_CLI_CONFIG_DOCKER_VERSION_DEFAULT = "1.40"
""" Default value for the docker client version number."""

METTA_LAUNCHPAD_VALIDATE_JSONSCHEMA = {
    "type": "object",
    "properties": {
        "config": {
            "type": ["object", "null"],
        },
        "mke": {
            "type": "object",
            "properties": {"endpoint": {"type": ["string", "null"]}},
        },
        "msr": {
            "type": "object",
            "properties": {"endpoint": {"type": ["string", "null"]}},
        },
        "cli": {
            "accept-license": {"type": "bool"},
            "disable-telemetry": {"type": "bool"},
        },
        "cluster_name": {"type": "string"},
        "config_file": {"type": "string"},
        "working_dir": {"type": "string"},
    },
    "required": ["config_file", "config", "mke"],
}
""" Validation jsonschema for terraform config contents """
METTA_LAUNCHPAD_VALIDATE_TARGET = {
    PLUGIN_ID_VALIDATE_JSONSCHEMA_SCHEMA_CONFIG_LABEL: METTA_LAUNCHPAD_VALIDATE_JSONSCHEMA
}
""" configerus validation target to match validate Launchpad config """

METTA_LAUNCHPAD_CONFIG_VALIDATE_JSONSCHEMA = {
    "type": "object",
    "properties": {
        "apiVersion": {"type": "string"},
        "kind": {"type": "string"},
        "hosts": {"type": "array", "items": {"type": "object"}},
        "spec": {
            "type": "object",
            "properties": {
                "mcr": {"type": "object"},
                "mke": {"type": "object"},
                "msr": {"type": "object"},
            },
            "required": ["mcr", "mke"],
        },
    },
    "required": ["apiVersion", "kind", "spec"],
}
""" Validation jsonschema for launchpad configuration """
METTA_LAUNCHPAD_CONFIG_VALIDATE_TARGET = {
    PLUGIN_ID_VALIDATE_JSONSCHEMA_SCHEMA_CONFIG_LABEL: METTA_LAUNCHPAD_CONFIG_VALIDATE_JSONSCHEMA
}
""" configerus jsonschema validation target for launchpad config """


# pylint: disable=too-many-instance-attributes
class LaunchpadProvisionerPlugin(ProvisionerBase):
    """Launchpad provisioner class.

    Use this to provision a system using Mirantis launchpad

    """

    def __init__(
        self,
        environment: Environment,
        instance_id: str,
        label: str = METTA_LAUNCHPAD_CONFIG_LABEL,
        base: Any = LOADED_KEY_ROOT,
    ):
        """Configure a new Launchpad provisioner plugin instance."""
        self._environment = environment
        """ Environemnt in which this plugin exists """
        self._instance_id = instance_id
        """ Unique id for this plugin instance """

        self.fixtures = Fixtures()
        """ keep a collection of fixtures that this provisioner creates """

        self.downloaded_bundle_users: List[str] = []
        """ track user bundles that have been downloaded to avoid unecessary repeats """

        self.config_label: str = label
        self.config_base: str = base

        """ load all of the launchpad configuration """
        launchpad_config_loaded = self._environment.config.load(label)

        # Run confgerus validation on the config using our above defined
        # jsonschema
        try:
            launchpad_config_loaded.get(base, validator=METTA_LAUNCHPAD_VALIDATE_TARGET)
        except ValidationError as err:
            raise ValueError("Launchpad config failed validation.") from err

        working_dir = launchpad_config_loaded.get(
            [base, METTA_LAUNCHPAD_CLI_WORKING_DIR_KEY]
        )
        """ if launchpad needs to be run in a certain path, set it with this config """
        if not os.path.isabs(working_dir):
            # did a relative path root get passed in as config?
            root_path = self.backend_output_name = launchpad_config_loaded.get(
                [base, METTA_LAUNCHPAD_CONFIG_ROOT_PATH_KEY]
            )
            if root_path:
                working_dir = os.path.join(root_path, working_dir)
            working_dir = os.path.abspath(working_dir)

        # decide on a path for the runtime launchpad.yml file
        self.config_file: str = launchpad_config_loaded.get(
            [base, METTA_LAUNCHPAD_CLI_CONFIG_FILE_KEY],
            default=METTA_LAUNCHPAD_CLI_CONFIG_FILE_DEFAULT,
        )
        if not os.path.isabs(self.config_file):
            # A relative [ath for the config file is expected to be relative to
            # the working dir]
            self.config_file = os.path.abspath(
                os.path.join(working_dir, self.config_file)
            )

        cluster_name_override = launchpad_config_loaded.get(
            [base, METTA_LAUNCHPAD_CLI_CLUSTEROVERRIDE_KEY], default=""
        )
        """ Can hardcode the cluster name if it can't be take from the yaml file """

        accept_license = launchpad_config_loaded.get(
            [base, METTA_LAUNCHPAD_CLI_ACCEPTLICENSE_KEY], default=True
        )
        """ should the client accept the license """
        disable_telemetry = launchpad_config_loaded.get(
            [base, METTA_LAUNCHPAD_CLI_DISABLETELEMETRY_KEY], default=True
        )
        """ should the client disable telemetry """
        disable_upgrade_check = launchpad_config_loaded.get(
            [base, METTA_LAUNCHPAD_CLI_DISABLETELEMETRYUPGRADECHECK_KEY], default=True
        )
        """ should the client disable upgrade checks """

        logger.debug("Creating Launchpad MKE client")
        self.client = LaunchpadClient(
            config_file=self.config_file,
            working_dir=working_dir,
            cluster_name_override=cluster_name_override,
            accept_license=accept_license,
            disable_telemetry=disable_telemetry,
            disable_upgrade_check=disable_upgrade_check,
        )

        # If we can, it makes sense to build the MKE and MSR client fixtures now.
        # This will only be possible in cases where we have an installed cluster.
        # We try that here, even though it is verbose and ugly, so that we have
        # the clients available for introspection, for all consumers.
        # We probably shouldn't, but it allows some flexibility.
        if os.path.exists(self.config_file):
            self._make_fixtures()

    def info(self, deep: bool = False) -> Dict[str, Any]:
        """Get info about a provisioner plugin.

        Returns:
        --------
        Dict of introspective information about this plugin_info

        """
        plugin = self
        client = self.client

        loaded = self._environment.config.load(self.config_label)

        info = {
            "plugin": {
                "config_label": plugin.config_label,
                "config_base": plugin.config_base,
                "downloaded_bundle_users": plugin.downloaded_bundle_users,
            },
            "client": {
                "cluster_name_override": client.cluster_name_override,
                "config_file": client.config_file,
                "working_dir": client.working_dir,
                "bin": client.bin,
            },
            "config": {
                "contents": loaded.get(self.config_base),
            },
        }

        if deep:
            try:
                info["config"]["interpreted"] = client.describe_config()
                info["bundles"] = {
                    user: client.bundle(user) for user in client.bundle_users()
                }

            # pylint: disable=broad-except
            except Exception:
                # There are many legitimate cases where this fails
                pass

        user = "admin"
        info["helper"] = {
            "commands": {
                "apply": f"{client.bin} apply -c {client.config_file}",
                "client-config": f"{client.bin} client-config -c {client.config_file} {user}",
            }
        }

        return info

    # pylint: disable=no-self-use
    def prepare(self):
        """Prepare the provisioning cluster for install.

        We ignore this.

        """
        logger.info("Running Launchpad Prepare().  Launchpad has no prepare stage.")

    def apply(self):
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
        try:
            logger.info("Using launchpad to install products onto backend cluster")
            self._write_launchpad_file()
            self.client.apply()
        except Exception as err:
            raise Exception("Launchpad failed to install") from err

        # Rebuild the fixture list now that we have installed
        self._make_fixtures(reload=True)

        # as we have likely changed MKE, let's make sure that a new client bundle
        # is downloaded.
        try:
            mke = self.fixtures.get_plugin(
                plugin_id=METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID,
            )
            mke.api_get_bundle(force=True)

        except KeyError as err:
            raise RuntimeError(
                "Launchpad MKE client failed to download client bundle."
            ) from err

    def destroy(self):
        """Ask the client to remove installed resources."""
        # tell the MKE client to remove its bundles
        try:
            mke = self.fixtures.get_plugin(
                plugin_id=METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID,
            )
            mke.rm_bundle()

        except KeyError as err:
            logger.warning(
                "Launchpad's MKE plugin failed do remove a client bundle: %s", err
            )

        # now tell the launchpad client to reset
        try:
            self.client.reset()

        except subprocess.CalledProcessError as err:
            logger.warning("Launchpad failed to destroy installed resources: %s", err)

    # ----- CLUSTER INTERACTION -----

    def _write_launchpad_file(self):
        """Write the config state to the launchpad file."""
        try:
            # load all of the launchpad configuration, force a reload to get up to date contents
            launchpad_loaded = self._environment.config.load(
                self.config_label, force_reload=True
            )
            launchpad_config: Dict[str, Any] = launchpad_loaded.get(
                [self.config_base, METTA_LAUNCHPAD_CONFIG_KEY],
                validator=METTA_LAUNCHPAD_CONFIG_VALIDATE_TARGET,
            )
        except KeyError as err:
            raise ValueError(
                "Could not find launchpad configuration from config."
            ) from err
        except ValidationError as err:
            raise ValueError("Launchpad config failed validation") from err

        # Our launchpad config differs slightly from the schema that launchpad
        # consumes, so we need a small conversion
        launchpad_config = self._convert_launchpad_config_to_file_format(
            launchpad_config
        )

        # write the launchpad output to our yaml file target (after creating
        # the path)
        os.makedirs(os.path.dirname(os.path.realpath(self.config_file)), exist_ok=True)
        with open(os.path.realpath(self.config_file), "w") as file:
            yaml.dump(launchpad_config, file)

    def _convert_launchpad_config_to_file_format(self, config):
        """Convert our launchpad config to the schema that launchpad uses."""
        # 1 discover the hosts counts
        hosts = []
        managers = []
        workers = []
        msrs = []
        for host in config["spec"]["hosts"]:
            hosts.append(host)
            if host["role"] == "manager":
                managers.append(host)
            if host["role"] == "worker":
                workers.append(host)
            if host["role"] == "msr":
                msrs.append(host)

        # convert install flags and update flags to lists from dicts
        def dtol(dic):
            """Convert dict flags to lists."""
            items: List[str] = []
            for key, value in dic.items():
                if value is True:
                    items.append(f"--{key}")
                else:
                    items.append(f"--{key}={value}")
            return items

        try:
            config["spec"]["mke"]["installFlags"] = dtol(
                config["spec"]["mke"]["installFlags"]
            )
        except KeyError:
            pass
        try:
            config["spec"]["mke"]["upgradeFlags"] = dtol(
                config["spec"]["mke"]["upgradeFlags"]
            )
        except KeyError:
            pass
        try:
            config["spec"]["msr"]["installFlags"] = dtol(
                config["spec"]["msr"]["installFlags"]
            )
        except KeyError:
            pass
        try:
            config["spec"]["msr"]["upgradeFlags"] = dtol(
                config["spec"]["msr"]["upgradeFlags"]
            )
        except KeyError:
            pass

        # xi32. is no msrs, then drop the msr block and force the type.
        if len(msrs) == 0:
            config["kind"] = "mke"
            config["spec"].pop("msr")

        return config

    # @TODO break this into many make client functions
    # pylint: disable=too-many-locals
    def _make_fixtures(self, user: str = "admin", reload: bool = False) -> Fixtures:
        """Build fixtures for all of the clients.

        Returns:
        --------
        Fixtures collection of fixtures that have been created

        """
        # get fresh values for the launchpad config (in case it has changed)
        launchpad_config = self._environment.config.load(
            self.config_label, force_reload=reload
        )

        # Retrieve a list of hosts, and use that to decide what clients to
        # make.  If we find a host for a client, then we retrieve needed
        # config and use it to generate the related client.
        hosts = launchpad_config.get(
            [self.config_base, METTA_LAUNCHPAD_CONFIG_HOSTS_KEY], default=[]
        )
        """ isolate the list of hosts so that we can separate them into roles """

        # MKE Client
        #
        mke_hosts = [host for host in hosts if host["role"] in ["manager"]]
        if len(mke_hosts) > 0:
            mke_api_accesspoint = launchpad_config.get(
                [self.config_base, METTA_LAUNCHPAD_CONFIG_MKE_ACCESSPOINT_KEY]
            )
            mke_api_username = launchpad_config.get(
                [self.config_base, METTA_LAUNCHPAD_CONFIG_MKE_USERNAME_KEY]
            )
            mke_api_password = launchpad_config.get(
                [self.config_base, METTA_LAUNCHPAD_CONFIG_MKE_PASSWORD_KEY]
            )
            mke_client_bundle_root = launchpad_config.get(
                [self.config_base, METTA_LAUNCHPAD_CONFIG_MKE_CLIENTBUNDLE_KEY],
                default=".",
            )

            mke_api_accesspoint = clean_accesspoint(mke_api_accesspoint)

            instance_id = (
                f"{self._instance_id}-{METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID}-{user}"
            )
            fixture = self._environment.add_fixture(
                plugin_id=METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID,
                instance_id=instance_id,
                priority=70,
                arguments={
                    "accesspoint": mke_api_accesspoint,
                    "username": mke_api_username,
                    "password": mke_api_password,
                    "hosts": mke_hosts,
                    "bundle_root": mke_client_bundle_root,
                },
                replace_existing=True,
            )
            self.fixtures.add(fixture, replace_existing=True)

        # MSR Client
        #
        msr_hosts = [host for host in hosts if host["role"] in ["msr"]]
        if len(msr_hosts) > 0:
            msr_api_accesspoint = launchpad_config.get(
                [self.config_base, METTA_LAUNCHPAD_CONFIG_MSR_ACCESSPOINT_KEY]
            )
            msr_api_username = launchpad_config.get(
                [self.config_base, METTA_LAUNCHPAD_CONFIG_MSR_USERNAME_KEY]
            )
            msr_api_password = launchpad_config.get(
                [self.config_base, METTA_LAUNCHPAD_CONFIG_MSR_PASSWORD_KEY]
            )

            msr_api_accesspoint = clean_accesspoint(msr_api_accesspoint)

            instance_id = (
                f"{self._instance_id}-{METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID}-{user}"
            )
            fixture = self._environment.add_fixture(
                plugin_id=METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID,
                instance_id=instance_id,
                priority=70,
                arguments={
                    "accesspoint": msr_api_accesspoint,
                    "username": msr_api_username,
                    "password": msr_api_password,
                    "hosts": msr_hosts,
                },
                replace_existing=True,
            )
            self.fixtures.add(fixture, replace_existing=True)

        # EXEC CLIENT
        #
        if len(hosts) > 0:
            instance_id = (
                f"{self._instance_id}-{METTA_LAUNCHPAD_EXEC_CLIENT_PLUGIN_ID}-{user}"
            )
            fixture = self._environment.add_fixture(
                plugin_id=METTA_LAUNCHPAD_EXEC_CLIENT_PLUGIN_ID,
                instance_id=instance_id,
                priority=69,
                arguments={"client": self.client},
                replace_existing=True,
            )
            self.fixtures.add(fixture, replace_existing=True)


def clean_accesspoint(accesspoint: str) -> str:
    """Remove any https:// and end / from an accesspoint."""
    accesspoint = accesspoint.replace("https://", "")
    return accesspoint
