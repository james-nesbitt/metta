
import os
import logging
import yaml
import json
import datetime
import subprocess
import shutil
from typing import Dict, List, Any

logger = logging.getLogger('metta_launchpad:launchpad')

METTA_LAUNCHPAD_CLI_CONFIG_FILE_DEFAULT = './launchpad.yml'
""" Launchpad config configuration file key """

METTA_LAUNCHPADCLIENT_WORKING_DIR_DEFAULT = '.'
""" Launchpad Client default working dir """
METTA_LAUNCHPADCLIENT_BIN_PATH = 'launchpad'
""" Launchpad bin exec for the subprocess """

METTA_USER_LAUNCHPAD_CLUSTER_PATH = os.path.expanduser(
    os.path.join('~', '.mirantis-launchpad', 'cluster'))
""" the str path to where launchpad keeps its user config """
METTA_USER_LAUNCHPAD_BUNDLE_SUBPATH = 'bundle'
""" str path to user bundle config can be found when it is downloaded """
METTA_USER_LAUNCHPAD_BUNDLE_META_FILE = 'meta.json'
""" str filename for the meta file in the client bundle path """


class LaunchpadClient:
    """ shell client for interacting with the launchpad bin """

    def __init__(self, config_file: str = METTA_LAUNCHPAD_CLI_CONFIG_FILE_DEFAULT,
                 working_dir: str = METTA_LAUNCHPADCLIENT_WORKING_DIR_DEFAULT,
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

        self.bin = METTA_LAUNCHPADCLIENT_BIN_PATH
        """ shell execution target for launchpad """

    def version(self):
        """ Output launchpad client version """
        self._run(['version'])

    def install(self):
        """ Install using the launchpad client """
        self._run(['apply'])

    def exec(self, host_index: int, cmds: List[str]):
        """ execute a command on a host index """
        client_config = self.describe_config()
        hosts = client_config['spec']['hosts']
        host = hosts[host_index]
        if 'ssh' in host:
            target = host['ssh']['address']
        if 'winrm' in host:
            target = host['winrm']['address']

        args = ['exec', '--target', target]
        args.extend(cmds)
        self._run(args)

    def exec_interactive(self, host_index: int, cmds: List[str]):
        """ execute a command on a host index """
        client_config = self.describe_config()
        hosts = client_config['spec']['hosts']
        host = hosts[host_index]
        if 'ssh' in host:
            target = host['ssh']['address']
        if 'winrm' in host:
            target = host['winrm']['address']
        args = ['exec', '--interactive', '--target', target]
        args.extend(cmds)
        self._run(args)

    def reset(self):
        """ Uninstall using the launchpad client """
        if os.path.isfile(self.config_file):
            self._run(['reset', '--force'])

    def register(self, name: str, email: str, company: str):
        """ Uninstall using the launchpad client """
        return self._run(['register', '--name', name,
                          '--email', email, '--company', company])

    def describe_config(self):
        """ Return the launchpad config report as umarshalled yaml """
        return yaml.safe_load(
            self._run(['describe', 'config'], return_output=True))

    def describe(self, report: str):
        """ Output one of the launchpad reports """
        self._run(['describe', report])

    def bundle_users(self):
        """ list bundle users which have been downloaded """
        return self._mke_client_downloaded_bundle_user_paths().keys()

    def bundle(self, user: str, reload: bool = False):
        """ Retrieve a client bundle and return the metadata as a dict """
        client_bundle_path = self._mke_client_bundle_path(user)
        client_bundle_meta_file = os.path.join(
            client_bundle_path, METTA_USER_LAUNCHPAD_BUNDLE_META_FILE)

        if reload or not os.path.isfile(client_bundle_meta_file):

            # @NOTE currently client bundle downloads are flaky.  They fail about 1/5 times
            #    with unclear TLS issues.  Because the failures are intermittent, we should
            #    just try again

            for i in range(1, 4):
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

        # Not sure why this isn't in there:
        data['Endpoints']['kubernetes']['kubeconfig'] = os.path.join(
            client_bundle_path, 'kube.yml')
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

    def rm_client_bundles(self):
        """ remove any downloaded client bundles """
        try:
            base = os.path.join(
                METTA_USER_LAUNCHPAD_CLUSTER_PATH,
                self._cluster_name(),
                METTA_USER_LAUNCHPAD_BUNDLE_SUBPATH)
        except BaseException:
            # most likely we could't determine a cluster_name, because we don't
            # have a config file.
            return

        if os.path.isdir(base):
            shutil.rmtree(base)

    def _mke_client_bundle_root(self):
        """  root path to the launchpad user conf """
        return os.path.join(
            METTA_USER_LAUNCHPAD_CLUSTER_PATH, self._cluster_name())

    def _mke_client_bundle_path(self, user: str):
        """ find the path to a client bundle for a user whether or not it has been downloaded """
        return os.path.join(METTA_USER_LAUNCHPAD_CLUSTER_PATH,
                            self._cluster_name(), METTA_USER_LAUNCHPAD_BUNDLE_SUBPATH, user)

    def _mke_client_downloaded_bundle_user_paths(self) -> Dict[str, str]:
        """ return a map of user names to downloaded bundle paths """
        try:
            base = os.path.join(
                METTA_USER_LAUNCHPAD_CLUSTER_PATH,
                self._cluster_name(),
                METTA_USER_LAUNCHPAD_BUNDLE_SUBPATH)
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
                "Launchpad yaml file had unexpected contents: {} : {}".format(
                    self.config_file, e)) from e

        if not isinstance(self.config_data, dict):
            raise ValueError(
                "Launchpad yaml file had unexpected contents: {}".format(self.config_file))

        try:
            return self.config_data['metadata']['name']
        except KeyError:
            raise ValueError(
                'Launchpad yaml file did not container a cluster name')

    def _run(self, args: List[str] = ['help'], return_output=False):
        """ Run a launchpad command

        Parameters:

        args (List[str]) : arguments to pass to the launchpad bin using
            subprocess

        """

        """ if the command passed uses a config file, add the flag for it """
        if not args[0] in ['help', 'version']:
            args = [args[0]] + ['-c', self.config_file] + args[1:]

        cmd = [self.bin] + args

        if return_output:
            logger.debug(
                "running launchpad command with output capture: %s",
                " ".join(cmd))
            exec = subprocess.run(
                cmd,
                cwd=self.working_dir,
                shell=False,
                stdout=subprocess.PIPE)
            exec.check_returncode()
            return exec.stdout.decode('utf-8')
        else:
            logger.debug("running launchpad command: %s", " ".join(cmd))
            exec = subprocess.run(
                cmd, cwd=self.working_dir, check=True, text=True)
            exec.check_returncode()
