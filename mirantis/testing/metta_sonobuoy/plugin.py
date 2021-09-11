"""

Sonobuoy plugin handling.

Struct abstraction for sonobuoy plugins.

"""
from typing import Dict, List, Any
import os.path

import yaml


class Plugin:
    """Plugin definition struct.

    This makes plugin abstraction easier for parametrizing the client.

    """

    def __init__(self, plugin_id: str, plugin_def: str = "", envs: Dict[str, str] = None):
        """Parametrize the plugin definition.

        Parameters:
        -----------
        id (str): what does sonobuoy think the plugin id will be

        def (str): plugin name or path to use with the -p flag

        envs (Dict[str, str]): Dict of plugin env variables set at run.
        """
        self.plugin_id: str = plugin_id
        self.plugin_def: str = plugin_def
        self.envs: Dict[str, str] = envs if envs is not None else {}

    def run_args(self) -> List[str]:
        """Provide cli run args for the plugin.

        Returns:
        --------
        A List of str args that can be used with the sonobuoy run command.
        """
        args: List[str] = []
        args += ["--plugin", self.plugin_def]

        for key in self.envs.keys():
            args += [f"--plugin-env={self.plugin_id}.{key}={self.envs[key]}"]

        return args

    # the deep argument is a standard for the info hook
    # pylint: disable=unused-argument
    def info(self, deep: bool = True) -> Dict[str, Any]:
        """Return a Dict of info about the plugin."""
        info = {"id": self.plugin_id, "def": self.plugin_def, "env": self.envs}

        if os.path.isfile(self.plugin_def):
            info["path"] = self.plugin_def
            with open(self.plugin_def, encoding="utf-8") as def_file:
                info["def"] = yaml.safe_load(def_file)

        return info
