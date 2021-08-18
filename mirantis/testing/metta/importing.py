"""

Dynamic python module loading

"""
import os.path
import sys
import logging
import importlib
from importlib.util import spec_from_file_location, module_from_spec
from importlib.machinery import ModuleSpec
from types import ModuleType
from typing import List, Union, Any

from configerus.config import Config
from configerus.loaded import LOADED_KEY_ROOT
from configerus.contrib.files import CONFIGERUS_PATH_KEY

logger = logging.getLogger("metta.import")

METTA_IMPORT_CONFIG_LABEL = "imports"
""" This config load() label is used to find modules to import """
METTA_IMPORT_CONFIG_IMPORTS_KEY = LOADED_KEY_ROOT
""" This config key is used to find modules to import """


def add_imports_from_config(
    config: Config,
    label: str = METTA_IMPORT_CONFIG_LABEL,
    base: Union[str, List[Any]] = METTA_IMPORT_CONFIG_IMPORTS_KEY,
):
    """Look in config for module imports.

    Use this if you want to dynamically import some modules defined in config.
    This can be used to load custom plugins that are decorated by the plugin
    Factory, but can include any module by path.

    @NOTE Modules are loaded by path, without a local namespace.

    Parameters:
    -----------
    config (Config) : config object to scan, and to add sources to

    label (str) : config label to load to search for sources
    base (str) : config key that should contain the list of sources

    """
    metta_config = config.load(label)

    imports_config = metta_config.get(base, default={})

    for import_name in imports_config:
        module_path = metta_config.get([base, import_name, CONFIGERUS_PATH_KEY])

        if os.path.isdir(module_path):
            module_path_dir = os.path.dirname(module_path)
            module_path_basename = os.path.basename(module_path)
            if not module_path_basename == import_name:
                logger.warning(
                    "Metta discovery importer cannot import a package (folder) using a"
                    "name other than the folder name: %s != %s",
                    module_path_basename,
                    import_name,
                )
            if module_path_dir not in sys.path:
                sys.path.append(module_path_dir)
            importlib.import_module(module_path_basename)
            logger.debug("Loaded package: %s : %s", module_path_basename, module_path)

        elif os.path.isfile(module_path):
            spec: ModuleSpec = spec_from_file_location(import_name, module_path)
            module: ModuleType = module_from_spec(spec)
            spec.loader.exec_module(module)
            logger.debug("Loaded module: %s : %s", import_name, module_path)

        else:
            raise ValueError(
                f"Could not import requested metta import {import_name} : {module_path}"
            )
