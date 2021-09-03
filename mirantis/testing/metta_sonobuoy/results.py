"""

Structures for interpreting Sonobuoy results.

"""
import os
import json
import logging
from enum import Enum, unique
from typing import List, Dict, Any
import subprocess

import yaml

logger = logging.getLogger("sonobuoy:results")


@unique
# pylint: disable=too-few-public-methods
class Status(Enum):
    """Enumerator to plugin states."""

    ERROR = "error"
    """ an error occured trying to interpret sonobuoy """
    PENDING = "pending"
    """ still pending """
    RUNNING = "running"
    """ testing is running """
    FAILED = "failed"
    """ testing has failed """
    COMPLETE = "complete"
    """ testing has completed without failure """
    PASSED = "passed"
    """ testing has passed """
    POSTPROCESS = "post-processing"
    """ testing has finished and is being processed """


class SonobuoyStatus:
    """A status output from the sonobuoy CLI."""

    def __init__(self, status_json: str):
        """Build from sonobuoy status results."""
        try:
            status = json.loads(status_json)
            self.status: Status = Status(status["status"])
            self.tar_info: str = status["tar-info"]

            self.plugins: Dict[str, Dict[str, Any]] = {}
            for plugin in status["plugins"]:
                self.plugins[plugin["plugin"]] = plugin

        except json.decoder.JSONDecodeError:
            logger.warning("json decoding of status failed: %s", status_json)
            self.status = Status.ERROR
            self.plugins = {}

    def plugin_list(self):
        """Retrieve the list of plugins."""
        return list(self.plugins.keys())

    def plugin(self, plugin: str):
        """Retrieve the results for one plugin."""
        return self.plugins[plugin]

    def plugin_status(self, plugin: str) -> "Status":
        """Get the status code for a plugin."""
        status_string = self.plugin(plugin)["status"]
        return Status(status_string)

    def __str__(self) -> str:
        """Convert to a string."""
        status: List[str] = []
        for plugin_id in self.plugin_list():
            status.append(f"{plugin_id}:{self.plugin_status(plugin_id)}")
        return f"[{']['.join(status)}]"


class SonobuoyResultsPluginItem:
    """An individual item from a sonobuoy results plugin."""

    def __init__(self, item_dict: Dict[str, Any]):
        """Single plugin result item."""
        self.name = item_dict["name"]
        self.status = Status(item_dict["status"])
        self.meta = item_dict["meta"]
        self.details = item_dict["details"] if "details" in item_dict else {}

    def meta_file_path(self):
        """Get the path to the error item file."""
        return self.meta["file"]

    def meta_file(self):
        """Get the contents of the file."""
        with open(self.meta_file_path(), encoding="utf8") as meta_file:
            return yaml.safe_load(meta_file)


class SonobuoyResultsPlugin:
    """The full results for a plugin."""

    def __init__(self, path: str):
        """Load results for a plugin results call."""
        with open(os.path.join(path, "sonobuoy_results.yaml"), encoding="utf8") as results_yaml:
            self.summary = yaml.safe_load(results_yaml)

    def name(self) -> str:
        """Return string name of plugin."""
        return self.summary["name"]

    def status(self) -> "Status":
        """Return the status object for the plugin results."""
        return Status(self.summary["status"])

    def __len__(self):
        """Count how many items are in the plugin_results."""
        return len(self.summary["items"])

    def __getitem__(self, instance_id: Any) -> SonobuoyResultsPluginItem:
        """Get item details from the plugin results."""
        return SonobuoyResultsPluginItem(item_dict=self.summary["items"][instance_id])


class SonobuoyResults:
    """Results retrieved analyzer."""

    def __init__(self, tarball: str, folder: str):
        """Interpret tarball contents."""
        logger.debug("un-tarring retrieved results: %s", tarball)
        res = subprocess.run(["tar", "-xzf", tarball, "-C", folder], check=True, text=True)
        res.check_returncode()

        self.results_path = folder

        with open(os.path.join(folder, "meta", "config.json"), encoding="utf8") as config_json:
            self.meta_config = json.load(config_json)
        with open(os.path.join(folder, "meta", "info.json"), encoding="utf8") as info_json:
            self.meta_info = json.load(info_json)
        with open(os.path.join(folder, "meta", "query-time.json"), encoding="utf8") as qt_json:
            self.meta_querytime = json.load(qt_json)

        self.plugins = []
        for plugin_id in self.meta_info["plugins"]:
            self.plugins.append(plugin_id)

    def plugin_list(self):
        """Return a string list of plugin ids."""
        return self.plugins

    def plugin(self, plugin_id) -> SonobuoyResultsPlugin:
        """Return the results for a single plugin."""
        return SonobuoyResultsPlugin(os.path.join(self.results_path, "plugins", plugin_id))
