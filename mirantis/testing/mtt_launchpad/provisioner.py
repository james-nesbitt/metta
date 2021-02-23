"""

Launchpad MTT provisioner pluging


Launchpad is a parasitic priovisioner as it does not create any infra
but rather it installs into an existing cluster defined by an output.

If your system is running before you run your test system then use the
uctt.contrib.dummy.provisioner provisioner and include the launchpad
config (yaml) in that provisioner configuration as an output. Otherwise
use a provisioner such as the terraform provisioner before this one.

"""

import json
import yaml
import datetime
import os.path
import subprocess
import logging
from typing import List, Dict, Any

from configerus.loaded import LOADED_KEY_ROOT

from uctt.plugin import UCTTPlugin, Type
from uctt.fixtures import Fixtures, UCCTFixturesPlugin
from uctt.provisioner import ProvisionerBase
from uctt.contrib.docker import UCTT_PLUGIN_ID_DOCKER_CLIENT
from uctt.contrib.kubernetes import UCTT_PLUGIN_ID_KUBERNETES_CLIENT

logger = logging.getLogger('mirantis.testing.mtt.provisioner:launchpad')

MTT_LAUNCHPAD_CONFIG_LABEL = 'launchpad'
""" Launchpad config label for configuration """
MTT_LAUNCHPAD_CONFIG_ROOT_PATH_KEY = 'root.path'
""" config key for a base path that should be used for any relative paths """
MTT_LAUNCHPAD_CLI_CONFIG_FILE_KEY = 'config_file'
""" Launchpad config cli key to tell us where to put the launchpad yml file """
MTT_LAUNCHPAD_CLI_WORKING_DIR_KEY = 'working_dir'
""" Launchpad config cli configuration working dir key """
MTT_LAUNCHPAD_CLI_WORKING_CLUSTEROVERRIDE = 'cluster_name'
""" If provided, this config key will override a cluster name pulled from yaml"""
MTT_LAUNCHPAD_CONFIG_OUTPUTSOURCE_LAUNCHPADFILE_OUTPUT_KEY = 'source_output.instance_id'
""" which config key will tell me the id of the backend output that will give me launchpad yml """
MTT_LAUNCHPAD_CLI_CONFIG_DOCKER_VERSION_DEFAULT = '1.40'
""" Default value for the docker client version number.  It would be best to discover or config this."""
MTT_LAUNCHPAD_BACKEND_OUTPUT_INSTANCE_ID_DEFAULT = 'mke_cluster'
""" Launchpad backend default output name for configuring launchpad """
MTT_LAUNCHPAD_CLI_CONFIG_FILE_DEFAULT = './launchpad.yml'
""" Launchpad config configuration file key """
MTT_LAUNCHPAD_CLI_CONFIG_ISINSTALLED = 'is_installed'
""" Boolean config value that tells the provisioner to try to load clients before running apply """


class LaunchpadProvisionerPlugin(ProvisionerBase, UCCTFixturesPlugin):
    """ Launchpad provisioner class

    Provision a system using Mirantis launchpad

    """

    def __init__(self, environment, instance_id,
                 label: str = MTT_LAUNCHPAD_CONFIG_LABEL, base: Any = LOADED_KEY_ROOT):
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

        self.working_dir = launchpad_config.get(
            [base, MTT_LAUNCHPAD_CLI_WORKING_DIR_KEY])
        """ if launchpad needs to be run in a certain path, set it with this config """
        if not self.working_dir:
            self.working_dir = MTT_LAUNCHPADCLIENT_WORKING_DIR_DEFAULT
        if not os.path.isabs(self.working_dir):
            # did a relative path root get passed in as config?
            root_path = self.backend_output_name = launchpad_config.get(
                [base, MTT_LAUNCHPAD_CONFIG_ROOT_PATH_KEY])
            if root_path:
                self.working_dir = os.path.join(root_path, self.working_dir)
            self.working_dir = os.path.abspath(self.working_dir)

        """ Retrieve the configuration for the output plugin """
        try:
            self.backend_output_name = launchpad_config.get(
                [base, MTT_LAUNCHPAD_CONFIG_OUTPUTSOURCE_LAUNCHPADFILE_OUTPUT_KEY], exception_if_missing=True)
            """ Backend provisioner give us this output as a source of launchpad yaml """
        except KeyError as e:
            raise ValueError(
                "Could not find launchpad configuration for backend provisioner output instance_id to get launchpad yml from.")

        # decide on a path for the runtime launchpad.yml file
        self.config_file = launchpad_config.get(
            [base, MTT_LAUNCHPAD_CLI_CONFIG_FILE_KEY], exception_if_missing=False)
        if not self.config_file:
            self.config_file = MTT_LAUNCHPAD_CLI_CONFIG_FILE_DEFAULT
        if not os.path.isabs(self.config_file):
            # A relative [ath for the config file is expected to be relative to
            # the working dir]
            self.config_file = os.path.abspath(
                os.path.join(self.working_dir, self.config_file))

        cluster_name_override = launchpad_config.get(
            [base, MTT_LAUNCHPAD_CLI_WORKING_CLUSTEROVERRIDE], exception_if_missing=False)
        """ Can hardcode the cluster name if it can't be take from the yaml file """

        logger.debug("Creating Launchpad API client")
        self.client = LaunchpadClient(
            config_file=self.config_file,
            working_dir=self.working_dir,
            cluster_name_override=cluster_name_override)

        if os.path.exists(self.config_file):
            try:
                self._make_fixtures()
                pass
            except BaseException:
                logger.debug(
                    "Launchpad couldn't initialize some plugins as we don't have enough information to go on.")
                # we most likely failed because we don't have enough info get
                # make fixtures from

    def info(self, provisioner: str = ''):
        """ get info about a provisioner plugin """
        plugin = self
        client = self.client
        return {
            'plugin': {
                'config_label': plugin.config_label,
                'config_base': plugin.config_base,
                'downloaded_bundle_users': plugin.downloaded_bundle_users,
                'working_dir': plugin.working_dir,
                'backend_output_name': plugin.backend_output_name
            },
            'client': {
                'cluster_name_override': client.cluster_name_override,
                'config_file': client.config_file,
                'working_dir': client.working_dir,
                'bin': client.bin
            },
            'bundles': {
                user: client.bundle(user) for user in client.bundle_users()
            },
            'helper': {
                'commands': {
                    'apply': "{workingpathcd}{bin} apply -c {config_file}".format(workingpathcd=("cd {} && ".format(client.working_dir) if not client.working_dir == '.' else ''), bin=client.bin, config_file=client.config_file),
                    'client-config': "{workingpathcd}{bin} client-config -c {config_file} {user}".format(workingpathcd=("cd {} && ".format(client.working_dir) if not client.working_dir == '.' else ''), bin=client.bin, config_file=client.config_file, user='admin')
                }
            }
        }

    def prepare(self):
        """ Prepare the provisioning cluster for install

        We ignore this.

        """
        logger.info(
            'Running Launchpad Prepare().  Launchpad has no prepare stage.')

    def apply(self):
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

        Raises:
        -------

        ValueError if the object has been configured (prepare) with config that
            doesn't work, or if the backend doesn't give valid yml

        Exception if launchpad fails.

        """

        # Get the backend output that holds laucnhpad yaml
        try:
            output = self.environment.fixtures.get_plugin(type=Type.OUTPUT,
                                                          instance_id=self.backend_output_name)
        except KeyError as e:
            raise Exception(
                "Launchpad could not retrieve YML configuration from the backend [{}] : ".format(self.backend_output_name, e)) from e
        if not output:
            raise ValueError(
                "Launchpad did not get necessary config from the backend output '%s'", self.backend_output_name)

        # if our output returns an output plugin (quack) then retrieve the
        # actual output
        if hasattr(output, 'get_output') and callable(
                getattr(output, 'get_output')):
            try:
                output = output.get_output()
            except AttributeError as e:
                raise ValueError(
                    'Backend output for launchpad yaml had not been given any data.  Are you sure that the backend ran?')
        if isinstance(output, dict):
            output = yaml.dump(output)

        # write the launchpad output to our yaml file target (after creating
        # the path)
        os.makedirs(
            os.path.dirname(
                os.path.realpath(
                    self.config_file)),
            exist_ok=True)
        with open(os.path.realpath(self.config_file), 'w') as file:
            file.write(output if output else '')

        try:
            logger.info(
                "Using launchpad to install products onto backend cluster")
            self.client.install()
        except Exception as e:
            raise Exception("Launchpad failed to install") from e

        self._make_fixtures(reload=True)

    def destroy(self):
        """ We don't bother uninstalling at this time """
        os.remove(self.config_file)

    """ CLUSTER INTERACTION """

    def _make_fixtures(self, user: str = 'admin',
                       reload: bool = False) -> Fixtures:
        """ Build fixtures for all of the clients """

        bundle_info = self._mke_client_bundle(user, reload)
        """ holds retrieved bundle information from MKE for all client configs. """

        # KUBE Client

        kube_config = os.path.join(bundle_info['path'], 'kube.yml')
        if not os.path.exists(kube_config):
            raise NotImplemented(
                "Launchpad was asked for a kubernetes client, but not kube config file was in the client bundle.  Are you sure this is a kube cluster?")

        instance_id = "launchpad-{}-{}-{}-client".format(
            self.instance_id, UCTT_PLUGIN_ID_KUBERNETES_CLIENT, user)
        fixture = self.environment.add_fixture(
            type=Type.CLIENT,
            plugin_id=UCTT_PLUGIN_ID_KUBERNETES_CLIENT,
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
            self.instance_id, UCTT_PLUGIN_ID_DOCKER_CLIENT, user)
        fixture = self.environment.add_fixture(
            type=Type.CLIENT,
            plugin_id=UCTT_PLUGIN_ID_DOCKER_CLIENT,
            instance_id=instance_id,
            priority=70,
            arguments={'host': host, 'cert_path': cert_path, 'version': MTT_LAUNCHPAD_CLI_CONFIG_DOCKER_VERSION_DEFAULT})
        self.fixtures.add_fixture(fixture)

    def _mke_client_bundle(self, user: str, reload: bool = False):
        """ Retrieve the MKE Client bundle metadata using the client """
        assert self.client, "Don't have a launchpad client configured yet"
        return self.client.bundle(user, reload)


MTT_LAUNCHPADCLIENT_WORKING_DIR_DEFAULT = '.'
""" Launchpad Client default working dir """
MTT_LAUNCHPADCLIENT_BIN_PATH = 'launchpad'
""" Launchpad bin exec for the subprocess """

MTT_USER_LAUNCHPAD_CLUSTER_PATH = os.path.expanduser(
    os.path.join('~', '.mirantis-launchpad', 'cluster'))
""" the str path to where launchpad keeps its user config """
MTT_USER_LAUNCHPAD_BUNDLE_SUBPATH = 'bundle'
""" str path to user bundle config can be found when it is downloaded """
MTT_USER_LAUNCHPAD_BUNDLE_META_FILE = 'meta.json'
""" str filename for the meta file in the client bundle path """


class LaunchpadClient:
    """ shell client for interacting with the launchpad bin """

    def __init__(self, config_file: str = MTT_LAUNCHPAD_CLI_CONFIG_FILE_DEFAULT,
                 working_dir: str = MTT_LAUNCHPADCLIENT_WORKING_DIR_DEFAULT,
                 cluster_name_override: str = ''):
        """
        Parameters:

        config_file (str) : path to launchpad config file, typically
            launchpad.yml

        working_dir (str) : full config file path.
            this typically plays a role in interpreting file paths from the
            config for things like ssh keys.  The client will use that path for
            python subprocess execution

        """
        self.config_file = config_file
        """ Path to config file """
        self.working_dir = working_dir
        """ Python subprocess working dir to execute launchpad in.
            This may be relevant in cases where ssh keys have a relative path """

        self.cluster_name_override = cluster_name_override
        """ if not empty this will be used as a cluster name instead of taking
            it from the yaml file """

        self.bin = MTT_LAUNCHPADCLIENT_BIN_PATH
        """ shell execution target for launchpad """

    def install(self):
        """ Install using the launchpad client """
        self._run(['apply'])

    def bundle_users(self):
        """ list bundle users which have been downloaded """
        return self._mke_client_downloaded_bundle_user_paths().keys()

    def bundle(self, user: str, reload: bool = False):
        """ Retrieve a client bundle and return the metadata as a dict """
        client_bundle_path = self._mke_client_bundle_path(user)
        client_bundle_meta_file = os.path.join(
            client_bundle_path, MTT_USER_LAUNCHPAD_BUNDLE_META_FILE)

        if reload or not os.path.isfile(client_bundle_meta_file):

            # @NOTE currently client bundle downloads are flaky.  They fail about 1/5 times
            #    with unclear TLS issues.  Because the failures are intermittent, we should
            #    just try again

            for i in range(1, 3):
                try:
                    self._run(["client-config", user])
                    break
                except Exception as e:
                    logger.warn(
                        "Attempt {} to download bundle.  Assuming flaky behaviour and trying again : {}".format(
                            i, e))

            else:
                raise Exception(
                    "Numerous attempts to download the client bundle have failed.")

        data = {}
        """ Will hold data pulled from the client meta data file """
        try:
            with open(client_bundle_meta_file) as json_file:
                data = json.load(json_file)
        except FileNotFoundError as e:
            raise ValueError(
                "failed to open the launchpad client bundle meta file.") from e

        # add some stuff that a client bundle always has
        data['path'] = client_bundle_path
        data['modified'] = datetime.datetime.fromtimestamp(
            os.path.getmtime(client_bundle_meta_file)).strftime("%Y-%m-%d %H:%M:%S")
        # this stuff should already be in the bundle, but it isn't
        data['tls_paths'] = {
            'docker': os.path.join(client_bundle_path, 'tls', 'docker'),
            'kubernetes': os.path.join(client_bundle_path, 'tls', 'kubernetes'),
        }

        return data

    def _mke_client_bundle_path(self, user: str):
        """ find the path to a client bundle for a user whether or not it has been downloaded """
        return os.path.join(MTT_USER_LAUNCHPAD_CLUSTER_PATH,
                            self._cluster_name(), MTT_USER_LAUNCHPAD_BUNDLE_SUBPATH, user)

    def _mke_client_downloaded_bundle_user_paths(self) -> Dict[str, str]:
        """ return a map of user names to dowqnloaded bundle paths """
        try:
            base = os.path.join(
                MTT_USER_LAUNCHPAD_CLUSTER_PATH,
                self._cluster_name(),
                MTT_USER_LAUNCHPAD_BUNDLE_SUBPATH)
            return {userdir: os.path.join(base, userdir) for userdir in os.listdir(
                base) if os.path.isdir(os.path.join(base, userdir))}
        except (ValueError, FileNotFoundError) as e:
            logger.debug(
                "Could not get user bundles names as there is no launchpad targets to check against.")
            return {}

    def _cluster_name(self):
        """ get the cluster name from the config file

        @TODO we should cache it, but then do we need to invalidate cache?

        """

        if self.cluster_name_override:
            return self.cluster_name_override

        try:
            with open(self.config_file) as config_file_object:
                self.config_data = yaml.load(
                    config_file_object, Loader=yaml.FullLoader)
                """ keep a parsed copy of the launchpad file """
        except FileNotFoundError as e:
            raise ValueError(
                "Launchpad yaml file could not be opened: {}".format(
                    self.config_file)) from e
        except Exception as e:
            raise ValueError(
                "Launchpad yaml file had unexpected contents: {}".format(
                    self.config_file)) from e

        if not isinstance(self.config_data, dict):
            raise ValueError(
                "Launchpad yaml file had unexpected contents: {}".format(self.config_file))

        try:
            return self.config_data['metadata']['name']
        except KeyError:
            raise ValueError(
                'Launchpad yaml file did not container a cluster name')

    def _run(self, args: List[str] = ['help']):
        """ Run a launchpad command

        Parameters:

        args (List[str]) : arguments to pass to the launchpad bin using
            subprocess

        """

        """ if the command passed uses a config file, add the flag for it """
        if not args[0] in ['help']:
            args = [args[0]] + ['-c', self.config_file] + args[1:]

        cmd = [self.bin] + args
        print("{}".format(cmd))
        exec = subprocess.run(cmd, cwd=self.working_dir)
        exec.check_returncode()
