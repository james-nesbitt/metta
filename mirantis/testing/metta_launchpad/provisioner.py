"""

Launchpad metta provisioner plugin.

Provisioner/Install  Mirantis products onto an existing cluster using
Launchpad.

"""
import os.path
import logging
from typing import Any, List, Dict

import yaml

from configerus.loaded import LOADED_KEY_ROOT
from configerus.contrib.jsonschema.validate import PLUGIN_ID_VALIDATE_JSONSCHEMA_SCHEMA_CONFIG_LABEL
from configerus.validator import ValidationError

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.fixtures import Fixtures
from mirantis.testing.metta.provisioner import ProvisionerBase
from mirantis.testing.metta.client import METTA_PLUGIN_TYPE_CLIENT
from mirantis.testing.metta_docker import METTA_PLUGIN_ID_DOCKER_CLIENT
from mirantis.testing.metta_kubernetes import METTA_PLUGIN_ID_KUBERNETES_CLIENT
from mirantis.testing.metta_mirantis import (METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID,
                                             METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID)

from .launchpad import LaunchpadClient, METTA_LAUNCHPAD_CLI_CONFIG_FILE_DEFAULT
from .exec_client import METTA_LAUNCHPAD_EXEC_CLIENT_PLUGIN_ID

logger = logging.getLogger('mirantis.testing.metta.provisioner:launchpad')

METTA_LAUNCHPAD_PROVISIONER_PLUGIN_ID = "metta_launchpad"
""" Metta plugin_id for the launchpad provisioner plugin """

METTA_LAUNCHPAD_CONFIG_LABEL = 'launchpad'
""" Launchpad config label for configuration """
METTA_LAUNCHPAD_CONFIG_ROOT_PATH_KEY = 'root.path'
""" config key for a base file path that should be used for any relative paths """
METTA_LAUNCHPAD_CONFIG_KEY = 'config'
""" which config key will provide the launchpad yml """
METTA_LAUNCHPAD_CONFIG_API_ACCESSPOINT_KEY = 'api.accesspoint'
""" config key for the API endpoint, usually the manager load-balancer """
METTA_LAUNCHPAD_CONFIG_API_USERNAME_KEY = 'api.username'
""" config key for the API username """
METTA_LAUNCHPAD_CONFIG_API_PASSWORD_KEY = 'api.password'
""" config key for the API password """
METTA_LAUNCHPAD_CONFIG_HOSTS_KEY = 'config.spec.hosts'
""" config key for the list of hosts as per the launchpad spec """
METTA_LAUNCHPAD_CLI_CONFIG_FILE_KEY = 'config_file'
""" Launchpad config cli key to tell us where to put the launchpad yml file """
METTA_LAUNCHPAD_CLI_WORKING_DIR_KEY = 'working_dir'
""" Launchpad config cli configuration working dir key """
METTA_LAUNCHPAD_CLI_CLUSTEROVERRIDE_KEY = 'cluster_name'
""" If provided, this config key will override a cluster name pulled from yaml"""
METTA_LAUNCHPAD_CLI_ACCEPTLICENSE_KEY = 'cli.accept-license'
""" If provided, this config key will tell the cli to accept the license"""
METTA_LAUNCHPAD_CLI_DISABLETELEMETRY_KEY = 'cli.disable-telemetry'
""" If provided, this config key will tell the cli to disable telemetry"""
METTA_LAUNCHPAD_CLI_DISABLETELEMETRYUPGRADECHECK_KEY = 'cli.disable-upgrade-check'
""" If provided, this config key will tell the cli to disable upgrade checks"""
METTA_LAUNCHPAD_CLI_CONFIG_DOCKER_VERSION_DEFAULT = '1.40'
""" Default value for the docker client version number."""

METTA_LAUNCHPAD_VALIDATE_JSONSCHEMA = {
    'type': 'object',
    'properties': {
        'config': {
            'type': ['object', 'null'],
        },
        'api': {
            'type': 'object',
            'properties': {
                'endpoint': {'type': ['string', 'null']}
            },
        },
        'cli': {
            'accept-license': {'type': 'bool'},
            'disable-telemetry': {'type': 'bool'},
        },
        'cluster_name': {
            'type': 'string'
        },
        'config_file': {
            'type': 'string'
        },
        'working_dir': {
            'type': 'string'
        }
    },
    'required': ['config_file', 'config', 'api']
}
""" Validation jsonschema for terraform config contents """
METTA_LAUNCHPAD_VALIDATE_TARGET = {
    PLUGIN_ID_VALIDATE_JSONSCHEMA_SCHEMA_CONFIG_LABEL: METTA_LAUNCHPAD_VALIDATE_JSONSCHEMA
}
""" configerus validation target to match validate Launchpad config """

METTA_LAUNCHPAD_CONFIG_VALIDATE_JSONSCHEMA = {
    'type': 'object',
    'properties': {
        'apiVersion': {'type': 'string'},
        'kind': {'type': 'string'},
        'hosts': {
            'type': 'array',
            'items': {
                'type': 'object'
            }
        },
        'spec': {
            'type': 'object',
            'properties': {
                'mcr': {'type': 'object'},
                'mke': {'type': 'object'},
                'msr': {'type': 'object'}
            },
            'required': ['mcr', 'mke']
        }
    },
    'required': ['apiVersion', 'kind', 'spec']
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

    def __init__(self, environment: Environment, instance_id: str,
                 label: str = METTA_LAUNCHPAD_CONFIG_LABEL, base: Any = LOADED_KEY_ROOT):
        """Configure a new Launchpad provisioner plugin instance."""
        self.environment = environment
        """ Environemnt in which this plugin exists """
        self.instance_id = instance_id
        """ Unique id for this plugin instance """

        self.fixtures = Fixtures()
        """ keep a collection of fixtures that this provisioner creates """

        self.downloaded_bundle_users: List[str] = []
        """ track user bundles that have been downloaded to avoid unecessary repeats """

        self.config_label: str = label
        self.config_base: str = base

        """ load all of the launchpad configuration """
        launchpad_config_loaded = self.environment.config.load(label)

        # Run confgerus validation on the config using our above defined
        # jsonschema
        try:
            launchpad_config_loaded.get(base, validator=METTA_LAUNCHPAD_VALIDATE_TARGET)
        except ValidationError as err:
            raise ValueError("Launchpad config failed validation.") from err

        working_dir = launchpad_config_loaded.get(
            [base, METTA_LAUNCHPAD_CLI_WORKING_DIR_KEY])
        """ if launchpad needs to be run in a certain path, set it with this config """
        if not os.path.isabs(working_dir):
            # did a relative path root get passed in as config?
            root_path = self.backend_output_name = launchpad_config_loaded.get(
                [base, METTA_LAUNCHPAD_CONFIG_ROOT_PATH_KEY])
            if root_path:
                working_dir = os.path.join(root_path, working_dir)
            working_dir = os.path.abspath(working_dir)

        # decide on a path for the runtime launchpad.yml file
        self.config_file: str = launchpad_config_loaded.get(
            [base, METTA_LAUNCHPAD_CLI_CONFIG_FILE_KEY],
            default=METTA_LAUNCHPAD_CLI_CONFIG_FILE_DEFAULT)
        if not os.path.isabs(self.config_file):
            # A relative [ath for the config file is expected to be relative to
            # the working dir]
            self.config_file = os.path.abspath(
                os.path.join(working_dir, self.config_file))

        cluster_name_override = launchpad_config_loaded.get(
            [base, METTA_LAUNCHPAD_CLI_CLUSTEROVERRIDE_KEY], default='')
        """ Can hardcode the cluster name if it can't be take from the yaml file """

        accept_license = launchpad_config_loaded.get(
            [base, METTA_LAUNCHPAD_CLI_ACCEPTLICENSE_KEY], default=True)
        """ should the client accept the license """
        disable_telemetry = launchpad_config_loaded.get(
            [base, METTA_LAUNCHPAD_CLI_DISABLETELEMETRY_KEY], default=True)
        """ should the client disable telemetry """
        disable_upgrade_check = launchpad_config_loaded.get(
            [base, METTA_LAUNCHPAD_CLI_DISABLETELEMETRYUPGRADECHECK_KEY], default=True)
        """ should the client disable upgrade checks """

        logger.debug("Creating Launchpad API client")
        self.client = LaunchpadClient(
            config_file=self.config_file,
            working_dir=working_dir,
            cluster_name_override=cluster_name_override,
            accept_license=accept_license,
            disable_telemetry=disable_telemetry,
            disable_upgrade_check=disable_upgrade_check)

        # If we can, it makes sense to build the docker and k8s client fixtures now.
        # This will only be possible in cases where we have an existing config file
        # and we can download a client bundle.
        # We try that here, even though it is verbose and ugly, so that we have
        # the clients available for introspection.
        # We probably shouldn't, but it allows some flexibility.
        if os.path.exists(self.config_file):
            try:
                self._make_fixtures()

            # We don't want this constructor to fail on a functionality test no matter the cause
            # pylint: disable=broad-except
            except BaseException:
                logger.debug("Could not create launchpad plugins on bootstrap.")
                # we most likely failed because we don't have enough info get
                # make fixtures from, as launchpad hasn't installed yet

    def info(self, deep: bool = False) -> Dict[str, Any]:
        """Get info about a provisioner plugin.

        Returns:
        --------
        Dict of introspective information about this plugin_info

        """
        plugin = self
        client = self.client

        loaded = self.environment.config.load(self.config_label)

        info = {
            'plugin': {
                'config_label': plugin.config_label,
                'config_base': plugin.config_base,
                'downloaded_bundle_users': plugin.downloaded_bundle_users
            },
            'client': {
                'cluster_name_override': client.cluster_name_override,
                'config_file': client.config_file,
                'working_dir': client.working_dir,
                'bin': client.bin
            },
            'config': {
                'contents': loaded.get(self.config_base),
            }
        }

        if deep:
            try:
                info['config']['interpreted'] = client.describe_config()
                info['bundles'] = {user: client.bundle(
                    user) for user in client.bundle_users()}

            # pylint: disable=broad-except
            except Exception:
                # There are many legitimate cases where this fails
                pass

            fixtures = {}
            for fixture in self.fixtures:
                fixture_info = {
                    'fixture': {
                        'plugin_type': fixture.plugin_type,
                        'plugin_id': fixture.plugin_id,
                        'instance_id': fixture.instance_id,
                        'priority': fixture.priority,
                    }
                }
                if hasattr(fixture.plugin, 'info'):
                    plugin_info = fixture.plugin.info()
                    if isinstance(plugin_info, dict):
                        fixture_info.update(plugin_info)
                fixtures[fixture.instance_id] = fixture_info
            info['fixtures'] = fixtures

        user = 'admin'
        info['helper'] = {
            'commands': {
                'apply': f"{client.bin} apply -c {client.config_file}",
                'client-config': f"{client.bin} client-config -c {client.config_file} {user}"
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

    def destroy(self):
        """Ask the client to remove installed resources."""
        self.client.reset()

    # ----- CLUSTER INTERACTION -----

    def _write_launchpad_file(self):
        """Write the config state to the launchpad file."""
        try:
            # load all of the launchpad configuration, force a reload to get up to date contents
            launchpad_config = self.environment.config.load(self.config_label, force_reload=True)
            launchpad_config = launchpad_config.get(
                [self.config_base, METTA_LAUNCHPAD_CONFIG_KEY],
                validator=METTA_LAUNCHPAD_CONFIG_VALIDATE_TARGET)
        except KeyError as err:
            raise ValueError("Could not find launchpad configuration from config.") from err
        except ValidationError as err:
            raise ValueError("Launchpad config failed validation") from err

        # write the launchpad output to our yaml file target (after creating
        # the path)
        os.makedirs(os.path.dirname(os.path.realpath(self.config_file)), exist_ok=True)
        with open(os.path.realpath(self.config_file), 'w') as file:
            yaml.dump(launchpad_config, file)

    # @TODO break this into many make client functions
    # pylint: disable=too-many-locals
    def _make_fixtures(self, user: str = 'admin', reload: bool = False) -> Fixtures:
        """Build fixtures for all of the clients.

        Returns:
        --------
        Fixtures collection of fixtures that have been created

        """
        # get fresh values for the launchpad config (in case it has changed)
        launchpad_config = self.environment.config.load(
            self.config_label, force_reload=reload)

        # holds retrieved bundle information from MKE for all client configs.
        bundle_info = self._mke_client_bundle(user, reload)

        # KUBE Client

        kube_config = os.path.join(bundle_info['path'], 'kube.yml')
        if not os.path.exists(kube_config):
            raise NotImplementedError(
                "Launchpad was asked for a kubernetes client, but not kube config file was in the "
                "client bundle.  Are you sure this is a kube cluster?")

        instance_id = f"{self.instance_id}-{METTA_PLUGIN_ID_KUBERNETES_CLIENT}-{user}"
        fixture = self.environment.add_fixture(
            METTA_PLUGIN_TYPE_CLIENT,
            plugin_id=METTA_PLUGIN_ID_KUBERNETES_CLIENT,
            instance_id=instance_id,
            priority=70,
            arguments={'kube_config_file': kube_config})
        # use the parent UCCTFixturesPlugin methods for adding fixtures
        self.fixtures.add(fixture)

        # DOCKER CLIENT
        #
        # @NOTE we pass in a docker API constraint because I ran into a case where the
        #   client failed because the python library was ahead in API version

        try:
            host = bundle_info['Endpoints']['docker']['Host']
            cert_path = bundle_info['tls_paths']['docker']
        except TypeError as err:
            logger.error(
                "Could not read client bundle properly: %s",
                bundle_info['Endpoints']['docker']['Host'])
            raise err

        instance_id = f"{self.instance_id}-{METTA_PLUGIN_ID_DOCKER_CLIENT}-{user}"
        fixture = self.environment.add_fixture(
            METTA_PLUGIN_TYPE_CLIENT,
            plugin_id=METTA_PLUGIN_ID_DOCKER_CLIENT,
            instance_id=instance_id,
            priority=70,
            arguments={'host': host, 'cert_path': cert_path,
                       'version': METTA_LAUNCHPAD_CLI_CONFIG_DOCKER_VERSION_DEFAULT})
        # use the parent UCCTFixturesPlugin methods for adding fixtures
        self.fixtures.add(fixture)

        # EXEC CLIENT
        #
        instance_id = f"{self.instance_id}-{METTA_LAUNCHPAD_EXEC_CLIENT_PLUGIN_ID}-{user}"
        fixture = self.environment.add_fixture(
            METTA_PLUGIN_TYPE_CLIENT,
            plugin_id=METTA_LAUNCHPAD_EXEC_CLIENT_PLUGIN_ID,
            instance_id=instance_id,
            priority=70,
            arguments={'client': self.client})
        # use the parent UCCTFixturesPlugin methods for adding fixtures
        self.fixtures.add(fixture)

        # The following clients both need the LB, username and password

        api_accesspoint = launchpad_config.get(
            [self.config_base, METTA_LAUNCHPAD_CONFIG_API_ACCESSPOINT_KEY])
        api_username = launchpad_config.get(
            [self.config_base, METTA_LAUNCHPAD_CONFIG_API_USERNAME_KEY])
        api_password = launchpad_config.get(
            [self.config_base, METTA_LAUNCHPAD_CONFIG_API_PASSWORD_KEY])

        hosts = launchpad_config.get(
            [self.config_base, METTA_LAUNCHPAD_CONFIG_HOSTS_KEY], default=[])
        """ isolate the list of hosts so that we can separate them into roles """

        # MKE Client
        #
        instance_id = f"{self.instance_id}-{METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID}-{user}"
        mke_hosts = [host for host in hosts if host['role'] in ['manager']]
        if len(mke_hosts) > 0:
            fixture = self.environment.add_fixture(
                METTA_PLUGIN_TYPE_CLIENT,
                plugin_id=METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID,
                instance_id=instance_id,
                priority=70,
                arguments={'accesspoint': api_accesspoint, 'username': api_username,
                           'password': api_password, 'hosts': mke_hosts})
            # use the parent UCCTFixturesPlugin methods for adding fixtures
            self.fixtures.add(fixture)

        # MSR Client
        #
        instance_id = f"{self.instance_id}-{METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID}-{user}"
        msr_hosts = [host for host in hosts if host['role'] in ['msr']]
        if len(msr_hosts) > 0:
            fixture = self.environment.add_fixture(
                METTA_PLUGIN_TYPE_CLIENT,
                plugin_id=METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID,
                instance_id=instance_id,
                priority=70,
                arguments={'accesspoint': None, 'username': api_username,
                           'password': api_password, 'hosts': msr_hosts})
            # use the parent UCCTFixturesPlugin methods for adding fixtures
            self.fixtures.add(fixture)

    def _mke_client_bundle(self, user: str, reload: bool = False):
        """Retrieve the MKE Client bundle metadata using the client."""
        assert self.client, "Don't have a launchpad client configured yet"
        return self.client.bundle(user, reload)
