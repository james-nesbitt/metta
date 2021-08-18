"""

Interact with the setuptools suite in a standardized way.

Functions:
----------

setuptools_entrypoint: run a setuptools entrypoint to bootstrap an argument
    using code provided by any python module.

"""
import logging
from typing import List, Dict, Any
from importlib import metadata

logger = logging.getLogger("metta.bootstrapp")

METTA_CONFIG_SETUPTOOLS_BOOTSTRAPS_KEY = "bootstraps"
"""Configerus .get() key for finding bootstrap entries."""


def setuptools_entrypoint(
    entrypoint: str, entries: List[str], args: List[Any], kwargs: Dict[str, Any]
):
    """Bootstrap some METTA objects with setuptools entrypoints.

    METTA bootstrapping is an attempt to allow an easy in to including
    contrib functionality without having to do a lot of Python imports.

    This is a setuptools enabled process, where any python package
    can declare a bootstraper, and this function will run that bootstrapper
    on request.
    The BootStrap entry_points are expected to receive a config object on
    which they can operate to add any specific or global functionality.

    BootStraps are typically used for two behaviours:

    1. just import files which run configerus or metta decorators to register
        plugins
    2. add source/formatter/validator plugins to the passed config object.

    Parameters:
    -----------
    bootstrap (List[str]) : a list of string bootstrapper entry_points for
        the ucct.bootstrap entry_points (part of setuptools.)
        Each value needs to refer to a valid entrypoint which will be
        executed with the config object as an argument.

    Raises:
    -------
    Raises a KeyError in cases of a bootstrap ID that cannot be found.

    Bootstrappers themselves may raise an exception.

    """
    for entry in entries:
        logger.debug("Running bootstrap entrypoint: %s=>%s ", entrypoint, entry)
        for metta_ep in metadata.entry_points()[entrypoint]:
            if metta_ep.name == entry:
                plugin = metta_ep.load()
                plugin(*args, **kwargs)
                break
        else:
            raise KeyError(f"Bootstrap not found {entrypoint}:{entry}")
