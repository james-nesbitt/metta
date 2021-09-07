"""

CLI client for running launchpad commands as an injectable class.

All of the metta plugijn functionality hands off to this module for actually
executing commands.

"""
import os
import logging
import json
import datetime
import subprocess
import shutil
from typing import Dict, List, Any

import yaml

logger = logging.getLogger("metta_launchpad:launchpad")

METTA_LAUNCHPAD_CLI_CONFIG_FILE_DEFAULT = "./launchpad.yml"
""" Launchpad config configuration file key """

METTA_LAUNCHPADCLIENT_WORKING_DIR_DEFAULT = "."
""" Launchpad Client default working dir """
METTA_LAUNCHPADCLIENT_BIN_PATH = "launchpad"
""" Launchpad bin exec for the subprocess """

METTA_USER_LAUNCHPAD_CLUSTER_PATH = os.path.expanduser(
    os.path.join("~", ".mirantis-launchpad", "cluster")
)
""" the str path to where launchpad keeps its user config """
METTA_USER_LAUNCHPAD_BUNDLE_SUBPATH = "bundle"
""" str path to user bundle config can be found when it is downloaded """
METTA_USER_LAUNCHPAD_BUNDLE_META_FILE = "meta.json"
""" str filename for the meta file in the client bundle path """

LAUNCHPAD_CLIENT_BUNDLE_RETRY_COUNT_DEFAULT = 2
""" default value for how many times we should retry client bundle download """


# yeah, this should probably get reduced.  Maybe combine the bools into a map
# pylint: disable=too-many-instance-attributes
class LaunchpadClient:
    """Shell client for interacting with the launchpad bin."""

    # this is what it takes to configure launchpad usage
    # pylint: disable=too-many-arguments
    def __init__(
        self,
        config_file: str = METTA_LAUNCHPAD_CLI_CONFIG_FILE_DEFAULT,
        working_dir: str = METTA_LAUNCHPADCLIENT_WORKING_DIR_DEFAULT,
        cluster_name_override: str = "",
        cli_options: Dict[str, bool] = None,
        binary: str = METTA_LAUNCHPADCLIENT_BIN_PATH,
    ):
        """Initialize LaunchpadClient object.

        Parameters:
        -----------
        config_file (str) : path to launchpad config file, typically
            launchpad.yml

        working_dir (str) : full config file path.
            this typically plays a role in interpreting file paths from the
            config for things like ssh keys.  The client will use that path for
            python subprocess execution

        cluster_name_override (str) : string name for the cluster which should
            be used instead of trying to read a value from config.  This can
            can help in some scenarios where config cannot be read outside of
            the client, and so cluster name is hard to discover.

        accept_license (bool) : passed to the launchpad client to tell it to
            accept the license on first use.

        cli_options (Dict[str, bool]) : Dict of boolean cli configuration keys:

            disable_telemetry (bool) : passed to the launchpad client to tell it to
                disable telemetry on actions taken.

            disable_upgrade_check (bool) : passed to the launchpad client to tell
                it to disable checking to see if a new client version is available.

            debug (bool) : passed to the launchpad client to tell it to enable
                verbose debugging output.

        """
        self.config_file: str = config_file
        """ Path to config file """
        self.working_dir: str = working_dir
        """ Python subprocess working dir to execute launchpad in.
            This may be relevant in cases where ssh keys have relative path """

        self.cluster_name_override: str = str(cluster_name_override).strip()
        """ if not empty this will be used as a cluster name instead of taking
            it from the yaml file """

        if shutil.which(binary) is None:
            raise ValueError(
                "Launchpad binary not found. Launchpad commands cannot be called. "
                f"Expected binary at path {binary}"
            )

        self.bin: str = binary
        """ shell execution target for launchpad """

        self.client_bundle_retry_count: int = int(LAUNCHPAD_CLIENT_BUNDLE_RETRY_COUNT_DEFAULT)
        """ how many times to rety a client bundle download """

        self.cli_options: Dict[str, bool] = cli_options if cli_options is not None else {}
        """Dict of global cli bool options that the client should include on calls."""

        self.debug: bool = False
        """ should launchpad be run with verbose output enabled ? """

    def info(self, deep: bool = False) -> Dict[str, Any]:
        """Get info about a provisioner plugin.

        Returns:
        --------
        Dict of introspective information about this plugin_info

        """
        # Start an info dict
        info: Dict[str, Any] = {
            "client": {
                "config_file": self.config_file,
                "working_dir": self.working_dir,
                "bin": self.bin,
            },
            "bundles": list(self.bundle_users()),
            "config": {},
        }

        try:
            with open(self.config_file, encoding="utf8") as conf_file_obj:
                info["config"]["contents"] = yaml.safe_load(conf_file_obj)
        except FileNotFoundError:
            pass

        if deep:
            try:
                info["config"]["interpreted"] = self.describe_config()
                info["bundles"] = {user: self.bundle(user) for user in self.bundle_users()}

            # pylint: disable=broad-except
            except Exception:
                # There are many legitimate cases where this fails
                pass

        return info

    def version(self):
        """Output launchpad client version."""
        self._run(["version"])

    def apply(self, debug: bool = False):
        """Install using the launchpad client."""
        self._run(["apply"], debug=debug)

    def exec(self, host_index: int, cmds: List[str]):
        """Execute a command on a host index."""
        client_config = self.describe_config()
        hosts = client_config["spec"]["hosts"]
        host = hosts[host_index]
        if "ssh" in host:
            target = host["ssh"]["address"]
        if "winrm" in host:
            target = host["winrm"]["address"]

        args = ["exec", "--target", target]
        args.extend(cmds)
        self._run(args)

    def exec_interactive(self, host_index: int, cmds: List[str]):
        """Execute a command on a host index."""
        client_config = self.describe_config()
        hosts = client_config["spec"]["hosts"]
        host = hosts[host_index]
        if "ssh" in host:
            target = host["ssh"]["address"]
        if "winrm" in host:
            target = host["winrm"]["address"]
        args = ["exec", "--interactive", "--target", target]
        args.extend(cmds)
        self._run(args)

    def reset(self):
        """Uninstall using the launchpad client."""
        if os.path.isfile(self.config_file):
            try:
                self._run(["reset", "--force"])
            except subprocess.TimeoutExpired:
                pass

    def register(self, name: str, email: str, company: str):
        """Uninstall using the launchpad client."""
        return self._run(["register", "--name", name, "--email", email, "--company", company])

    def describe_config(self):
        """Return the launchpad config report as umarshalled yaml."""
        return yaml.safe_load(self._run(["describe", "config"], return_output=True))

    def describe(self, report: str):
        """Output one of the launchpad reports."""
        self._run(["describe", report])

    def bundle_users(self):
        """List bundle users which have been downloaded."""
        return self._mke_client_downloaded_bundle_user_paths().keys()

    def get_bundle(self, user: str, reload: bool = True):
        """Retrieve the client bundle from the MKE endpoint."""
        client_bundle_path = self._mke_client_bundle_path(user)
        client_bundle_meta_file = os.path.join(
            client_bundle_path, METTA_USER_LAUNCHPAD_BUNDLE_META_FILE
        )

        if reload or not os.path.isfile(client_bundle_meta_file):

            # @NOTE currently client bundle downloads are flaky.  They fail about 1/5 times
            #    with unclear TLS issues.  Because the failures are intermittent, we should
            #    just try again

            for i in range(1, self.client_bundle_retry_count):
                try:
                    self._run(["client-config", user])
                    break
                except subprocess.CalledProcessError as err:
                    logger.warning(
                        "Attempt %s to download bundle failed.  Assuming flaky "
                        "behaviour and trying again : %s",
                        i,
                        err,
                    )

            else:
                raise RuntimeError("Numerous attempts to download the client bundle failed.")

    def bundle(self, user: str):
        """Interpret the bundle metadata as a dict.

        @NOTE why doesn't this download the bundle automatically?

        We avoid including a bundle download in this step as we need to have an option
        for trying to detect the bundle without getting any timeout type errors.
        This method can be used as a quick fail attempt to decide if launchpad has
        installed on the cluster, but checking to see if a client bundle has been
        downloaded.
        If you perform an action, you should consider asking for the client bundle.

        """
        client_bundle_path: str = self._mke_client_bundle_path(user)
        client_bundle_meta_file: str = os.path.join(
            client_bundle_path, METTA_USER_LAUNCHPAD_BUNDLE_META_FILE
        )
        # Will hold data pulled from the client meta data file
        data: Dict[str, Any] = {}
        try:
            with open(client_bundle_meta_file, encoding="utf8") as json_file:
                data = json.load(json_file)

                # helm complains if this file has loose permissions
                client_bundle_kubeconfig_file = os.path.join(client_bundle_path, "kube.yml")
                os.chmod(client_bundle_kubeconfig_file, 0o600)
        except FileNotFoundError as err:
            raise ValueError(
                f"failed to open the launchpad client bundle meta "
                f"file : {client_bundle_meta_file}"
            ) from err

        # Not sure why this isn't in there:
        data["Endpoints"]["kubernetes"]["kubeconfig"] = client_bundle_kubeconfig_file
        # add some stuff that a client bundle always has
        data["path"] = client_bundle_path
        data["modified"] = datetime.datetime.fromtimestamp(
            os.path.getmtime(client_bundle_meta_file)
        ).strftime("%Y-%m-%d %H:%M:%S")
        # this stuff should already be in the bundle, but it isn't
        data["tls_paths"] = {
            "docker": os.path.join(client_bundle_path, "tls", "docker"),
            "kubernetes": os.path.join(client_bundle_path, "tls", "kubernetes"),
        }

        return data

    def rm_client_bundles(self):
        """Remove any downloaded client bundles."""
        base: str = os.path.join(
            METTA_USER_LAUNCHPAD_CLUSTER_PATH,
            self._cluster_name(),
            METTA_USER_LAUNCHPAD_BUNDLE_SUBPATH,
        )

        if os.path.isdir(base):
            shutil.rmtree(base)

    def _mke_client_bundle_root(self):
        """Root path to the launchpad user conf."""
        return os.path.join(METTA_USER_LAUNCHPAD_CLUSTER_PATH, self._cluster_name())

    def _mke_client_bundle_path(self, user: str) -> str:
        """Find the path to a client bundle for a user."""
        return os.path.join(
            METTA_USER_LAUNCHPAD_CLUSTER_PATH,
            self._cluster_name(),
            METTA_USER_LAUNCHPAD_BUNDLE_SUBPATH,
            user,
        )

    def _mke_client_downloaded_bundle_user_paths(self) -> Dict[str, str]:
        """Return a map of user names to downloaded bundle paths."""
        try:
            base: str = os.path.join(
                METTA_USER_LAUNCHPAD_CLUSTER_PATH,
                self._cluster_name(),
                METTA_USER_LAUNCHPAD_BUNDLE_SUBPATH,
            )
            return {
                userdir: os.path.join(base, userdir)
                for userdir in os.listdir(base)
                if os.path.isdir(os.path.join(base, userdir))
            }
        except (ValueError, FileNotFoundError):
            logger.debug(
                "Could not get user bundles names as there are"
                " no launchpad targets to check against."
            )
            return {}

    def _cluster_name(self):
        """Get the cluster name from the config file.

        @TODO we should cache it, but then do we need to invalidate cache?

        """
        if self.cluster_name_override:
            return str(self.cluster_name_override)

        try:
            with open(self.config_file, encoding="utf8") as config_file_object:
                # keep a parsed copy of the launchpad file
                config_data = yaml.safe_load(config_file_object)
        except FileNotFoundError as err:
            raise ValueError(
                "Launchpad yaml file could not be opened" f": {self.config_file}"
            ) from err
        except Exception as err:
            raise ValueError(
                "Launchpad yaml file had unexpected contents:" f" {self.config_file}"
            ) from err

        if not isinstance(config_data, dict):
            raise ValueError(f"Launchpad yaml file had unexpected contents: {self.config_file}")

        try:
            return str(config_data["metadata"]["name"])
        except KeyError as err:
            raise ValueError("Launchpad yaml file did not contain a cluster name") from err

    def _run(self, args: List[str], return_output=False, debug: bool = False):
        """Run a launchpad command.

        Parameters:
        -----------
        args (List[str]) : arguments to pass to the launchpad bin using
            subprocess

        return_output (bool) : this call should capture the exec output and
            return it instead of sending it to stdout

        debug (bool) : override class debug value if True

        """
        # if the command passed uses a config file, add the flag for it
        if not args[0] in ["help", "version"]:
            args = [args[0]] + ["-c", self.config_file] + args[1:]

        cmd = [self.bin]

        cmd += [args[0]]

        if debug or self.debug:
            cmd += ["--debug"]
        if "disable-telemetry" in self.cli_options and self.cli_options["disable-telemetry"]:
            cmd += ["--disable-telemetry"]
        if "accept-license" in self.cli_options and self.cli_options["accept-license"]:
            cmd += ["--accept-license"]
        if (
            "disable-upgrade-check" in self.cli_options
            and self.cli_options["disable-upgrade-check"]
        ):
            cmd += ["--disable-upgrade-check"]

        if len(args) > 1:
            cmd += args[1:]

        # makes it more readable
        # pylint: disable=no-else-return
        if return_output:
            logger.debug("running launchpad command with output capture: %s", " ".join(cmd))
            return_res = subprocess.run(
                cmd,
                cwd=self.working_dir,
                shell=False,
                check=True,
                stdout=subprocess.PIPE,
            )
            return_res.check_returncode()
            return return_res.stdout.decode("utf-8")

        else:
            logger.debug("running launchpad command: %s", " ".join(cmd))
            res = subprocess.run(cmd, cwd=self.working_dir, check=True, text=True)
            res.check_returncode()
            return res
