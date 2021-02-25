"""

METTA Core toolset

In this module, the root package, are found a number of tool plugin constructors
that can be used to get instances of the plugins based on either passed in data
or configerus config.

The contstruction.py module does the heavy lifting of building plugins and
PluginInstances sets.

"""

from typing import List
import logging

from configerus import new_config as configerus_new_config
from configerus.config import Config

from .environment import Environment

logger = logging.getLogger('metta')

""" METTA and Configerus bootstrapping """

FIXED_CONFIGERUS_BOOSTRAPS = [
    "deep",
    "get",
    "jsonschema",
    "files"
]
""" configerus bootstraps that we will use on config objects """
FIXED_METTA_BOOTSTRAPS = [
    "metta_validation",
    "metta_dummy",
    "metta_common"
]
DEFAULT_ADDITIONAL_METTA_BOOTSTRAPS = [
    "metta_ansible",
    "metta_docker",
    "metta_kubernetes",
    "metta_terraform"
]
""" default overridable metta bootstrap calls """

DEFAULT_ENVIRONMENT_NAME = 'default'
""" If you don't ask for a particular environment, you are going to get this one """

""" Environments """

_environments = {}
""" Keep a Dict of all created environments for introspection """


def new_environment(name: str = DEFAULT_ENVIRONMENT_NAME, additional_metta_bootstraps: List[str] = DEFAULT_ADDITIONAL_METTA_BOOTSTRAPS,
                    additional_configerus_bootstraps: List[str] = []):
    """ Make new environment object

    First create a config object, then use it to create an environment
    object.

    Parameters
    ----------

    additional_metta_bootstraps (List[str]) : run additiional metta bootstraps
        on the config object.  Defaults to the metta bootstrap.

    additional_configerus_bootstraps (List[str]) : run additional configerus
        bootstrap entry_points

    Returns:
    --------

    An initialized Environment object with a new configerus Config object

    """
    configerus_bootstraps = FIXED_CONFIGERUS_BOOSTRAPS + \
        additional_configerus_bootstraps
    config = configerus_new_config(bootstraps=configerus_bootstraps)

    return new_environment_from_config(
        name=name, config=config, additional_metta_bootstraps=additional_metta_bootstraps)


def new_environment_from_config(config: Config,
                                name: str = DEFAULT_ENVIRONMENT_NAME, additional_metta_bootstraps: List[str] = DEFAULT_ADDITIONAL_METTA_BOOTSTRAPS):
    """ Make a new environment from an existing configerus.Config object

    Use a passed configerus Config object to create an environment object,
    register the env and then return it.

    The config object is bootstrapped before we create the environment.

    Parameters
    ----------

    additional_metta_bootstraps (List[str]) : run additiional metta bootstraps
        on the config object.  Defaults to the metta bootstrap.

    additional_configerus_bootstraps (List[str]) : run additional configerus
        bootstrap entry_points

    Returns:
    --------

    An intialized Environment object from the config

    """
    global _environments

    environment = Environment(config=config)

    metta_bootstraps = FIXED_METTA_BOOTSTRAPS + additional_metta_bootstraps
    environment.bootstrap(metta_bootstraps)

    if name in _environments:
        logger.warn(
            "Existing environment '{}' is being overwritten".format(name))
    _environments[name] = environment
    return environment


def environment_names() -> List[str]:
    """ Return a list of all of the created environments """
    return list(_environments)


def has_environment(name: str) -> bool:
    """ Does an environment already exist with a passed name """
    return name in _environments.keys()


def get_environment(name: str = DEFAULT_ENVIRONMENT_NAME) -> Environment:
    """ Return an environment that has already been created """
    try:
        return _environments[name]
    except KeyError as e:
        raise KeyError(
            "Requested environment has not yet been created: {}".format(name)) from e
