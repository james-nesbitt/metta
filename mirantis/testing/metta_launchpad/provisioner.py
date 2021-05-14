"""

Launchpad metta provisioner plugin

"""

import json
import yaml
import os.path
import logging
from typing import List, Dict, Any

from configerus.loaded import LOADED_KEY_ROOT
from configerus.contrib.jsonschema.validate import PLUGIN_ID_VALIDATE_JSONSCHEMA_SCHEMA_CONFIG_LABEL
from configerus.validator import ValidationError

from mirantis.testing.metta.plugin import METTAPlugin, Type
from mirantis.testing.metta.fixtures import Fixtures, UCCTFixturesPlugin
from mirantis.testing.metta.provisioner import ProvisionerBase
from mirantis.testing.metta_docker import METTA_PLUGIN_ID_DOCKER_CLIENT
from mirantis.testing.metta_kubernetes import METTA_PLUGIN_ID_KUBERNETES_CLIENT
from mirantis.testing.metta_mirantis import METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID, METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID

from .launchpad import LaunchpadClient, METTA_USER_LAUNCHPAD_CLUSTER_PATH, METTA_LAUNCHPAD_CLI_CONFIG_FILE_DEFAULT
from .exec_client import METTA_LAUNCHPAD_EXEC_CLIENT_PLUGIN_ID

logger = logging.getLogger('mirantis.testing.metta.provisioner:launchpad')

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
""" Default value for the docker client version number.  It would be best to discover or config this."""

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
""" configerus validation target to matche the above config, which relates to the bootstrap in __init__.py """

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
""" configerus jsonschema validation target for validation launchpad config file structure """


class LaunchpadProvisionerPlugin(ProvisionerBase, UCCTFixturesPlugin):
    """ Launchpad provisioner class

    Provision a system using Mirantis launchpad

    """

    def __init__(self, environment, instance_id,
                 label: str = METTA_LAUNCHPAD_CONFIG_LABEL, base: Any = LOADED_KEY_ROOT):
        """ Run the super constructor but also set class properties """
        ProvisionerBase.__init__(self, environment, instance_id)
        UCCTFixturesPlugin.__init__(self)

        """ Set an empty client, populated after the backend is provisioned """
        self.client = None
        """ A configured LaunchpadClient """

        self.downloaded_bundle_users = []
        """ track user bundles that have been downloaded to avoid unecessary repeats """

        self.config_label = label
        self.config_base = base

        """ load all of the launchpad configuration """
        launchpad_config = self.environment.config.load(label)

        # Run confgerus validation on the config using our above defined
        # jsonschema
        try:
            launchpad_config.get(
                base, validator=METTA_LAUNCHPAD_VALIDATE_TARGET)
        except ValidationError as e:
            raise ValueError(
                "Launchpad config failed validation: {}".format(e)) from e

        self.working_dir = launchpad_config.get(
            [base, METTA_LAUNCHPAD_CLI_WORKING_DIR_KEY])
        """ if launchpad needs to be run in a certain path, set it with this config """
        if not self.working_dir:
            self.working_dir = METTA_LAUNCHPADCLIENT_WORKING_DIR_DEFAULT
        if not os.path.isabs(self.working_dir):
            # did a relative path root get passed in as config?
            root_path = self.backend_output_name = launchpad_config.get(
                [base, METTA_LAUNCHPAD_CONFIG_ROOT_PATH_KEY])
            if root_path:
                self.working_dir = os.path.join(root_path, self.working_dir)
            self.working_dir = os.path.abspath(self.working_dir)

        """ Retrieve the configuration the client plugin """
        try:
            self.launchpad_config = launchpad_config.get(
                [base, METTA_LAUNCHPAD_CONFIG_KEY])
            """ config source of launchpad yaml """
        except KeyError as e:
            raise ValueError(
                "Could not find launchpad configuration.")

        # decide on a path for the runtime launchpad.yml file
        self.config_file = launchpad_config.get(
            [base, METTA_LAUNCHPAD_CLI_CONFIG_FILE_KEY], default=METTA_LAUNCHPAD_CLI_CONFIG_FILE_DEFAULT)
        if not os.path.isabs(self.config_file):
            # A relative [ath for the config file is expected to be relative to
            # the working dir]
            self.config_file = os.path.abspath(
                os.path.join(self.working_dir, self.config_file))

        cluster_name_override = launchpad_config.get(
            [base, METTA_LAUNCHPAD_CLI_CLUSTEROVERRIDE_KEY], default='')
        """ Can hardcode the cluster name if it can't be take from the yaml file """

        accept_license = launchpad_config.get(
            [base, METTA_LAUNCHPAD_CLI_ACCEPTLICENSE_KEY], default=True)
        """ should the client accept the license """
        disable_telemetry = launchpad_config.get(
            [base, METTA_LAUNCHPAD_CLI_DISABLETELEMETRY_KEY], default=True)
        """ should the client disable telemetry """
        disable_upgrade_check = launchpad_config.get(
            [base, METTA_LAUNCHPAD_CLI_DISABLETELEMETRYUPGRADECHECK_KEY], default=True)
        """ should the client disable upgrade checks """

        logger.debug("Creating Launchpad API client")
        self.client = LaunchpadClient(
            config_file=self.config_file,
            working_dir=self.working_dir,
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
            except BaseException:
                logger.debug(
                    "Launchpad couldn't initialize some plugins as we don't have enough information to go on.")
                # we most likely failed because we don't have enough info get
                # make fixtures from

    def info(self, deep: bool = False):
        """ get info about a provisioner plugin """
        plugin = self
        client = self.client

        info = {
            'plugin': {
                'config_label': plugin.config_label,
                'config_base': plugin.config_base,
                'downloaded_bundle_users': plugin.downloaded_bundle_users,
                'working_dir': plugin.working_dir,
            },
            'client': {
                'cluster_name_override': client.cluster_name_override,
                'config_file': client.config_file,
                'working_dir': client.working_dir,
                'bin': client.bin
            },
            'config': {
                'contents': self.launchpad_config,
            }
        }

        if deep:
            try:
                info['config']['interpreted'] = client.describe_config()
                info['bundles'] = {user: client.bundle(
                    user) for user in client.bundle_users()}
            except Exception:
                pass

            fixtures = {}
            for fixture in self.get_fixtures().to_list():
                fixture_info = {
                    'fixture': {
                        'type': fixture.type.value,
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

        info['helper'] = {
            'commands': {
                'apply': "{bin} apply -c {config_file}".format(workingpathcd=("cd {} && ".format(client.working_dir) if not client.working_dir == '.' else ''), bin=client.bin, config_file=client.config_file),
                'client-config': "{bin} client-config -c {config_file} {user}".format(workingpathcd=("cd {} && ".format(client.working_dir) if not client.working_dir == '.' else ''), bin=client.bin, config_file=client.config_file, user='admin')
            }
        }

        return info

    def prepare(self):
        """ Prepare the provisioning cluster for install

        We ignore this.

        """
        logger.info(
            'Running Launchpad Prepare().  Launchpad has no prepare stage.')

    def apply(self, debug: bool = False):
        """ bring a cluster up

        We assume that the cluster is running and the we can pull the required
        yaml from an output fixture in the environment.

        This plugin needs an output fixture, probably of dict type.  It will
        Pull that structure for the launchpad yaml config file and dump it into
        its config path.
        The provisioner can find an output directly from the environment, or
        from a specific fixture source.  If you want the output to come from
        only a specific backend fixture then make sure that a "backend" config
        exists, otherwise just use an "output" config.

        Parameters:
        -----------

        debug (bool) : override config value for Debug if True, make the launc
            pad call more verbose

        Raises:
        -------

        ValueError if the object has been configured (prepare) with config that
            doesn't work, or if the backend doesn't give valid yml

        Exception if launchpad fails.

        """

        try:
            logger.info(
                "Using launchpad to install products onto backend cluster")
            self._write_launchpad_file()
            self.client.apply(debug=debug)
        except Exception as e:
            raise Exception("Launchpad failed to install: {}".format(e)) from e

        # Rebuild the fixture list now that we have installed
        self._make_fixtures(reload=True)

    def destroy(self, quick: bool = False):
        """ Ask the client to remove installed resources """
        self.client.reset(quick=quick)

    """ CLUSTER INTERACTION """

    def _write_launchpad_file(self):
        """ write the config state to the launchpad file """
        try:
            """ load all of the launchpad configuration, force a reload to get up to date contents """
            launchpad_config = self.environment.config.load(
                self.config_label, force_reload=True)
            self.launchpad_config = launchpad_config.get(
                [self.config_base, METTA_LAUNCHPAD_CONFIG_KEY], validator=METTA_LAUNCHPAD_CONFIG_VALIDATE_TARGET)
            """ config source of launchpad yaml """
        except KeyError as e:
            raise ValueError(
                "Could not find launchpad configuration from config.")
        except ValidationError as e:
            raise ValueError(
                "Launchpad config failed validation: {}".format(e)) from e

        # write the launchpad output to our yaml file target (after creating
        # the path)
        os.makedirs(
            os.path.dirname(
                os.path.realpath(
                    self.config_file)),
            exist_ok=True)
        with open(os.path.realpath(self.config_file), 'w') as file:
            yaml.dump(self.launchpad_config, file)

    def _make_fixtures(self, user: str = 'admin',
                       reload: bool = False) -> Fixtures:
        """ Build fixtures for all of the clients """

        launchpad_config = self.environment.config.load(
            self.config_label, force_reload=reload)
        """ get fresh values for the launchpad config (in case it has changed) """

        bundle_info = self._mke_client_bundle(user, reload)
        """ holds retrieved bundle information from MKE for all client configs. """

        # KUBE Client

        kube_config = os.path.join(bundle_info['path'], 'kube.yml')
        if not os.path.exists(kube_config):
            raise NotImplemented(
                "Launchpad was asked for a kubernetes client, but not kube config file was in the client bundle.  Are you sure this is a kube cluster?")

        instance_id = "launchpad-{}-{}-{}-client".format(
            self.instance_id, METTA_PLUGIN_ID_KUBERNETES_CLIENT, user)
        fixture = self.environment.add_fixture(
            type=Type.CLIENT,
            plugin_id=METTA_PLUGIN_ID_KUBERNETES_CLIENT,
            instance_id=instance_id,
            priority=70,
            arguments={'kube_config_file': kube_config})
        self.fixtures.add_fixture(fixture)

        # DOCKER CLIENT
        #
        # @NOTE we pass in a docker API constraint because I ran into a case where the
        #   client failed because the python library was ahead in API version

        try:
            host = bundle_info['Endpoints']['docker']['Host']
            cert_path = bundle_info['tls_paths']['docker']
        except TypeError as e:
            logger.error(
                "Could not read client bundle properly: %s",
                bundle_info['Endpoints']['docker']['Host'])
            raise e

        instance_id = "launchpad-{}-{}-{}-client".format(
            self.instance_id, METTA_PLUGIN_ID_DOCKER_CLIENT, user)
        fixture = self.environment.add_fixture(
            type=Type.CLIENT,
            plugin_id=METTA_PLUGIN_ID_DOCKER_CLIENT,
            instance_id=instance_id,
            priority=70,
            arguments={'host': host, 'cert_path': cert_path, 'version': METTA_LAUNCHPAD_CLI_CONFIG_DOCKER_VERSION_DEFAULT})
        self.fixtures.add_fixture(fixture)

        # EXEC CLIENT
        #
        instance_id = "launchpad-{}-{}-{}-client".format(
            self.instance_id, METTA_LAUNCHPAD_EXEC_CLIENT_PLUGIN_ID, user)
        fixture = self.environment.add_fixture(
            type=Type.CLIENT,
            plugin_id=METTA_LAUNCHPAD_EXEC_CLIENT_PLUGIN_ID,
            instance_id=instance_id,
            priority=70,
            arguments={'client': self.client})
        self.fixtures.add_fixture(fixture)

        # The following clients both need the LB, username and password

        api_accesspoint = self.launchpad_config = launchpad_config.get(
            [self.config_base, METTA_LAUNCHPAD_CONFIG_API_ACCESSPOINT_KEY])
        api_username = self.launchpad_config = launchpad_config.get(
            [self.config_base, METTA_LAUNCHPAD_CONFIG_API_USERNAME_KEY])
        api_password = self.launchpad_config = launchpad_config.get(
            [self.config_base, METTA_LAUNCHPAD_CONFIG_API_PASSWORD_KEY])

        hosts = self.launchpad_config = launchpad_config.get(
            [self.config_base, METTA_LAUNCHPAD_CONFIG_HOSTS_KEY], default=[])
        """ isolate the list of hosts so that we can separate them into roles """

        # MKE Client
        #
        instance_id = "launchpad-{}-{}-{}-client".format(
            self.instance_id, METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID, user)
        mke_hosts = [host for host in hosts if host['role'] in ['manager']]
        if len(mke_hosts) > 0:
            fixture = self.environment.add_fixture(
                type=Type.CLIENT,
                plugin_id=METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID,
                instance_id=instance_id,
                priority=70,
                arguments={'accesspoint': api_accesspoint, 'username': api_username, 'password': api_password, 'hosts': mke_hosts})
            self.fixtures.add_fixture(fixture)

        # MSR Client
        #
        instance_id = "launchpad-{}-{}-{}-client".format(
            self.instance_id, METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID, user)
        msr_hosts = [host for host in hosts if host['role'] in ['msr']]
        if len(msr_hosts) > 0:
            fixture = self.environment.add_fixture(
                type=Type.CLIENT,
                plugin_id=METTA_MIRANTIS_CLIENT_MSR_PLUGIN_ID,
                instance_id=instance_id,
                priority=70,
                arguments={'accesspoint': None, 'username': api_username, 'password': api_password, 'hosts': msr_hosts})
            self.fixtures.add_fixture(fixture)

    def _mke_client_bundle(self, user: str, reload: bool = False):
        """ Retrieve the MKE Client bundle metadata using the client """
        assert self.client, "Don't have a launchpad client configured yet"
        return self.client.bundle(user, reload)
