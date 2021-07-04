"""

Metta provisioner plugin for testkit.

A provisioner plugin that uses testkit to create infra
and optionally to install either kubernetes or Mirantis
MKE/MSR onto the infra.

"""
import logging
import os
from typing import Any, Dict, List
from subprocess import CalledProcessError

import yaml

from configerus.loaded import LOADED_KEY_ROOT
from configerus.contrib.jsonschema.validate import (
    PLUGIN_ID_VALIDATE_JSONSCHEMA_SCHEMA_CONFIG_LABEL,
)
from configerus.validator import ValidationError

from mirantis.testing.metta.fixtures import Fixtures
from mirantis.testing.metta.provisioner import ProvisionerBase
from mirantis.testing.metta.client import METTA_PLUGIN_INTERFACE_ROLE_CLIENT
from mirantis.testing.metta_mirantis import (
    METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID,
    METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID,
)

from .testkit import TestkitClient, TESTKITCLIENT_CLI_CONFIG_FILE_DEFAULT

logger = logging.getLogger("testkit.provisioner")

METTA_PLUGIN_ID_TESTKIT_PROVISIONER = "metta_testkit"
""" Metta plugin id for testkit provisioner plugins """

TESTKIT_PROVISIONER_CONFIG_LABEL = "testkit"
TESTKIT_PROVISIONER_CONFIG_BASE = LOADED_KEY_ROOT
""" configerus config label/base-key for loading testkit provisioner config """

TESTKIT_CONFIG_KEY_SYSTEMNAME = "system_name"
""" config key to find the system name """
TESTKIT_CONFIG_KEY_CREATE_OPTIONS = "options.create"
""" config key to find where the testkit create options """
TESTKIT_CONFIG_KEY_CONFIG = "config"
""" config key to find where to put the testkit config file data/contents """
TESTKIT_CONFIG_KEY_INSTANCES = "instances"
""" config key to find what instances to spec out (build) """
TESTKIT_CONFIG_KEY_CONFIGFILE = "config_file"
""" config key to find where to put the testkit config file """
TESTKIT_CONFIG_DEFAULT_CONFIGFILE = TESTKITCLIENT_CLI_CONFIG_FILE_DEFAULT
""" default value for where to put the testkit config file """

METTA_TESTKIT_CONFIG_MKE_ACCESSPOINT_KEY = "mke.accesspoint"
""" config key for the MKE endpoint, usually the manager load-balancer """
METTA_TESTKIT_CONFIG_MKE_USERNAME_KEY = "mke.username"
""" config key for the MKE username """
METTA_TESTKIT_CONFIG_MKE_PASSWORD_KEY = "mke.password"
""" config key for the MKE password """
METTA_TESTKIT_CONFIG_MKE_CLIENTBUNDLE_KEY = "mke.client_bundle_root"
""" Config key for the MKE client bundle root path """

METTA_TESTKIT_CONFIG_MSR_ACCESSPOINT_KEY = "msr.accesspoint"
""" config key for the MSR endpoint, usually a load-balancer """
METTA_TESTKIT_CONFIG_MSR_USERNAME_KEY = "msr.username"
""" config key for the MSR username """
METTA_TESTKIT_CONFIG_MSR_PASSWORD_KEY = "msr.password"
""" config key for the MSR password """

METTA_TESTKIT_CONFIG_VALIDATE_JSONSCHEMA = {
    "type": "object",
    "properties": {
        "ucp": {"type": "object"},
        "dtr": {"type": "object"},
        "": {"type": "object"},
    },
    "required": [],
}
""" Validation jsonschema for testkit configuration for testkit yaml files """
METTA_TESTKIT_CONFIG_VALIDATE_TARGET = {
    PLUGIN_ID_VALIDATE_JSONSCHEMA_SCHEMA_CONFIG_LABEL: METTA_TESTKIT_CONFIG_VALIDATE_JSONSCHEMA
}
""" configerus jsonschema validation target for testkit config file """

METTA_TESTKIT_PROVISIONER_CONFIG_VALIDATE_JSONSCHEMA = {
    "type": "object",
    "properties": {
        "opts": {"type": "object"},
        "config": METTA_TESTKIT_CONFIG_VALIDATE_JSONSCHEMA,
    },
    "required": [],
}
""" Validation jsonschema for provisioner configuration """
METTA_TESTKIT_PROVISIONER_CONFIG_VALIDATE_TARGET = {
    PLUGIN_ID_VALIDATE_JSONSCHEMA_SCHEMA_CONFIG_LABEL: METTA_TESTKIT_PROVISIONER_CONFIG_VALIDATE_JSONSCHEMA
}
""" configerus jsonschema validation target for the provisioner plugin """


# pylint: disable=too-many-instance-attributes
class TestkitProvisionerPlugin(ProvisionerBase):
    """Testkit provisioner plugin.

    Provisioner plugin that allows control of and interaction with a testkit
    cluster.

    ## Requirements

    1. this plugin uses subprocess to call a testkit binary, so you have to
       install testkit in the environment

    ## Usage

    @TODO

    """

    def __init__(
        self,
        environment,
        instance_id,
        label: str = TESTKIT_PROVISIONER_CONFIG_LABEL,
        base: Any = TESTKIT_PROVISIONER_CONFIG_BASE,
    ):
        """Initialize Testkit provisioner.

        Parameters:
        -----------
        environment (Environment) : metta environment object that this plugin
            is attached.
        instance_id (str) : label for this plugin instances.

        label (str) : config load label for plugin configuration.
        base (str) : config base for loaded config for plugin configuration.

        """
        self._environment = environment
        """ Environemnt in which this plugin exists """
        self._instance_id = instance_id
        """ Unique id for this plugin instance """

        self.fixtures = Fixtures()
        """ Keep a collection of all fixtures created by this plugin """

        logger.info("Preparing Testkit setting")

        self.config_label = label
        """ configerus load label that should contain all of the config """
        self.config_base = base

        testkit_config = self._environment.config.load(
            self.config_label, force_reload=True
        )
        """ load the plugin configuration so we can retrieve options """

        self.system_name = testkit_config.get(
            [self.config_base, TESTKIT_CONFIG_KEY_SYSTEMNAME]
        )
        """ hat will testkit call the system """

        try:
            testkit_config = self._environment.config.load(self.config_label)
            """ loaded plugin configuration label """
        except KeyError as err:
            raise ValueError(
                "Testkit plugin configuration did not have any config"
            ) from err

        # instances = testkit_config.get([self.config_base, TESTKIT_CONFIG_KEY_INSTANCES])
        # """ what instances to create """

        self.config_file = testkit_config.get(
            [self.config_base, TESTKIT_CONFIG_KEY_CONFIGFILE],
            default=TESTKIT_CONFIG_DEFAULT_CONFIGFILE,
        )
        """ config_file value from plugin configuration """
        self.testkit = TestkitClient(config_file=self.config_file)
        """ testkit client object """

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
        plugin = self
        client = self.testkit
        testkit_config = self._environment.config.load(self.config_label)

        info = {
            "plugin": {
                "config_label": plugin.config_label,
                "config_base": plugin.config_base,
                "system_name": self.system_name,
            },
            "client": {
                "config_file": client.config_file,
                "working_dir": client.working_dir,
                "bin": client.bin,
                "version": client.version(),
            },
            # 'instances': testkit_config.get([self.config_base, TESTKIT_CONFIG_KEY_INSTANCES]),
            "config": testkit_config.get([self.config_base, TESTKIT_CONFIG_KEY_CONFIG]),
        }

        if deep:
            hosts: List[Dict[str, Any]] = []
            try:
                for node in self.testkit.machine_ls(self.system_name):
                    hosts.append(node)
            except CalledProcessError:
                pass
            info["hosts"] = hosts

        return info

    def prepare(self):
        """Prepare any needed resources.

        We don't create the testkit file here so that it is created as late as
        possible.  This allows more options for dynamic config sources in the
        testkit config.

        """

    def apply(self):
        """Create the testkit yaml file and run testkit to create a cluster."""
        self._write_config_file()

        testkit_config = self._environment.config.load(
            self.config_label, force_reload=True
        )
        """ load the plugin configuration so we can retrieve options """
        opts = testkit_config.get(
            [self.config_base, TESTKIT_CONFIG_KEY_CREATE_OPTIONS], default={}
        )
        """ retrieve testkit client options from config """
        opt_list = []
        for key, value in opts.items():
            if isinstance(value, str):
                opt_list.append(f'--{key}="{value}"')
            else:
                opt_list.append(f"--{key}={value}")

        # run the testkit client command to provisioner the cluster
        self.testkit.create(opts=opt_list)

        # Now that we have created a cluster, make the relevant client plugins.
        self.make_fixtures()

        # as we have likely changed MKE, let's make sure that a new client bundle
        # is downloaded.
        try:
            mke = self.fixtures.get_plugin(
                plugin_id=METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID,
            )
            mke.api_get_bundle(force=True)
            mke.make_bundle_clients()

        except KeyError as err:
            raise RuntimeError(
                "Launchpad MKE client failed to download client bundle."
            ) from err

    def destroy(self):
        """Destroy any created resources."""
        # run the testkit client command to provisioner the cluster
        self.testkit.system_rm(self.system_name)
        self._rm_config_file()

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
        if not os.access(self.config_file, os.R_OK):
            return

        testkit_config = self._environment.config.load(
            self.config_label, force_reload=True
        )
        """ load the plugin configuration so we can retrieve options """
        testkit_hosts = self.testkit.machine_ls(system_name=self.system_name)
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

        # If MSR/DTR is to be installed then it gets installed to the first worker
        # Node, so we should pick that node as a host for the client.
        # This is all just how testkit works.
        if testkit_config.get(
            [self.config_base, TESTKIT_CONFIG_KEY_CREATE_OPTIONS, "dtr"], default=False
        ):
            msr_hosts.append(worker_hosts[0])

        if len(mke_hosts) > 0:
            mke_api_username = testkit_config.get(
                [self.config_base, METTA_TESTKIT_CONFIG_MKE_USERNAME_KEY]
            )
            mke_api_password = testkit_config.get(
                [self.config_base, METTA_TESTKIT_CONFIG_MKE_PASSWORD_KEY]
            )
            mke_client_bundle_root = testkit_config.get(
                [self.config_base, METTA_TESTKIT_CONFIG_MKE_CLIENTBUNDLE_KEY],
                default=".",
            )

            instance_id = (
                f"{self._instance_id}-{METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID}"
                f"-{mke_api_username}"
            )
            fixture = self._environment.add_fixture(
                METTA_PLUGIN_INTERFACE_ROLE_CLIENT,
                plugin_id=METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID,
                instance_id=instance_id,
                priority=70,
                arguments={
                    "accesspoint": None,
                    "username": mke_api_username,
                    "password": mke_api_password,
                    "hosts": mke_hosts,
                    "bundle_root": mke_client_bundle_root,
                },
            )
            self.fixtures.add(fixture)

            # We got an MKE client, so let's activate it.
            fixture.plugin.api_get_bundle(force=True)
            fixture.plugin.make_bundle_clients()

        else:
            logger.warning("No MKE master hosts found, not creating an MKE client.")

        if len(msr_hosts) > 0:
            msr_api_username = testkit_config.get(
                [self.config_base, METTA_TESTKIT_CONFIG_MSR_USERNAME_KEY]
            )
            msr_api_password = testkit_config.get(
                [self.config_base, METTA_TESTKIT_CONFIG_MSR_PASSWORD_KEY]
            )

            instance_id = (
                f"{self._instance_id}-{METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID}"
                f"-{msr_api_username}"
            )
            fixture = self._environment.add_fixture(
                METTA_PLUGIN_INTERFACE_ROLE_CLIENT,
                plugin_id=METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID,
                instance_id=instance_id,
                priority=70,
                arguments={
                    "accesspoint": None,
                    "username": msr_api_username,
                    "password": msr_api_password,
                    "hosts": msr_hosts,
                    "protocol": "http",
                },
            )
            # Yes, testkit exposes MSR using http, not https
            self.fixtures.add(fixture)

    def _write_config_file(self):
        """Write the config file for testkit."""
        try:
            # load all of the testkit configuration, force a reload to get up to date contents
            testkit_config = self._environment.config.load(
                self.config_label, force_reload=True
            )
            config = testkit_config.get(
                [self.config_base, TESTKIT_CONFIG_KEY_CONFIG],
                validator=METTA_TESTKIT_CONFIG_VALIDATE_TARGET,
            )
            """ config source of launchpad yaml """
        except KeyError as err:
            raise ValueError(
                "Could not find launchpad configuration from config."
            ) from err
        except ValidationError as err:
            raise ValueError("Launchpad config failed validation") from err

        # write the configto our yaml file target (creating the path)
        os.makedirs(os.path.dirname(os.path.realpath(self.config_file)), exist_ok=True)
        with open(os.path.realpath(self.config_file), "w") as file:
            yaml.dump(config, file)

    def _rm_config_file(self):
        """Remove the written config file."""
        if os.path.isfile(self.config_file):
            os.remove(self.config_file)
