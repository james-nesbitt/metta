"""

METTA Core toolset

In this module, the root package, are found a number of tool plugin constructors
that can be used to get instances of the plugins based on either passed in data
or configerus config.

The contstruction.py module does the heavy lifting of building plugins and
PluginInstances sets.

"""

import os
import sys
from typing import List
import logging
import importlib
import time

from configerus import new_config as configerus_new_config
from configerus.config import Config
from configerus.loaded import LOADED_KEY_ROOT

from .discover import discover_project_root, discover_sources_from_config, discover_imports, METTA_CONFIG_LABEL
from .environment import Environment, METTA_PLUGIN_CONFIG_LABEL_ENVIRONMENTS

logger = logging.getLogger('metta')

""" METTA and Configerus bootstrapping """

FIXED_CONFIGERUS_BOOSTRAPS = [
    "get",
    "env",
    "jsonschema",
    "files"
]
""" configerus bootstraps that we will use on config objects. We use functionality
    in the core which heavily depends on this config, so it is necessary """
FIXED_METTA_BOOTSTRAPS = [
    "metta_common"
]
""" Metta bootstraps to apply to any created environemnt.  We use functionality
    in the core which heavily depends on these, so they are necessary """
DEFAULT_ADDITIONAL_METTA_BOOTSTRAPS = [
    "metta_ansible",
    "metta_docker",
    "metta_dummy",
    "metta_kubernetes",
    "metta_terraform"
]
""" default metta bootstrap calls to add to any created cluster """

DEFAULT_ENVIRONMENT_NAME = 'default'
""" If you don't provide a particular environment name, you are going to get this one """

CWD = os.path.realpath(os.getcwd())
""" CWD if needed for project discovery """

""" Environments """

_environments = {}
""" Keep a Dict of all created environments for introspection """


def discover(path: str = CWD, additional_configerus_bootstraps: List[str] = [
], additional_metta_bootstraps: List[str] = DEFAULT_ADDITIONAL_METTA_BOOTSTRAPS):
    """ Mega entrypoint into Metta - discover project config, environment and fixtures

    If you want to just write some config and get defined config and environments, use this.

    This will:

    1. create a new config object
    2. look for 'metta.yml|json' files which tell it where your project root is.
    3. add projects roots as config sources
    4. look for config that tells it to add more config sources
    5. look for config that tells it to import some python modules
    6. look for config that tells it to create some environments

    You should have:

    1. a metta.yml file in your project root (should not be empty)
        a. if you don't want to keep config in your project root then declare an
           additional config source for a config path
    2. an environments.yml file to declare environments and environment fixtures.


    Returns:
    --------

    Nothing.  This will create environments, which you can access by name.

    """
    logger.info("Creating project from path {}".format(path))
    configerus_bootstraps = FIXED_CONFIGERUS_BOOSTRAPS + \
        additional_configerus_bootstraps
    config = configerus_new_config(bootstraps=configerus_bootstraps)

    # Look for project root, and root config (and look in that root config for
    # stuff to do)
    discover_project_config(config=config, path=path)
    # Create any environments defined in config

    metta_config = config.load('metta')

    if metta_config.has(['environments', 'from_config']):
        environment_config = metta_config.get(['environments', 'from_config'])
        label = environment_config['label'] if 'label' in environment_config else 'metta'
        base = environment_config['base'] if 'base' in environment_config else LOADED_KEY_ROOT
        new_environments_from_config(
            config=config,
            additional_metta_bootstraps=additional_metta_bootstraps,
            label=label,
            base=base)

    elif metta_config.has(['environments', 'from_builder']):
        environment_config = metta_config.get(['environments', 'from_builder'])
        module = environment_config['import']
        method = environment_config['method']
        new_environments_from_builder(
            config=config,
            additional_metta_bootstraps=additional_metta_bootstraps,
            module=module,
            method=method)

    elif metta_config.has('environments'):
        new_environments_from_config(
            config=config,
            additional_metta_bootstraps=additional_metta_bootstraps,
            label='metta',
            base='environments')


def discover_project_config(config: Config, path: str = CWD):
    """ Discover project root and root config

    We start of by scanning the path, and all of its parents for a metta.yml
    file.  We collect all of the paths as config sources, into a config object.

    We ask the config object if there are any additional config sources to add
    after adding all of the root config sources.

    We ask the config object for information about required python imports to
    allow local code to be imported.  This can be used to allow plugin
    registration.

    Parameters:
    -----------

    path (str) : we will be scanning path/parents looking for some configuration
      for meta.  With this argument you can suggest the starting poing for the
      scan.

    additional_configerus_bootstraps (List[str]) : run additional configerus
        bootstrap entry_points

    """
    logger.info("Discovering project config from path {}".format(path))

    # First see if we can find a root metta.yml file for file context
    # if we do, then we add config sources for such paths
    discover_project_root(config, path)
    # existing config may be able to tell us to add more config sources
    discover_sources_from_config(config)
    # import any module imports requested
    discover_imports(config)


def new_environment(name: str = DEFAULT_ENVIRONMENT_NAME, additional_metta_bootstraps: List[str] = DEFAULT_ADDITIONAL_METTA_BOOTSTRAPS,
                    additional_configerus_bootstraps: List[str] = [], load_more_from_label: str = '', load_more_from_base: str = LOADED_KEY_ROOT):
    """ Make new environment object after making a new config

    First create a config object, then use it to create an environment
    object.

    Parameters
    ----------

    additional_metta_bootstraps (List[str]) : run additiional metta bootstraps
        on the config object.  Defaults to the metta bootstrap.

    additional_configerus_bootstraps (List[str]) : run additional configerus
        bootstrap entry_points

    # Optionally tell the environment to get more information about itself from
    # a config label/key root

    load_more_from_label (str) : Config label to load to get more info about the environment

    load_more_from_base (str) : Config key to .get() as a base for more info about the environment

    Returns:
    --------

    An initialized Environment object with a new configerus Config object

    """
    logger.info("Creating single environment from config")
    configerus_bootstraps = FIXED_CONFIGERUS_BOOSTRAPS + \
        additional_configerus_bootstraps
    config = configerus_new_config(bootstraps=configerus_bootstraps)

    metta_bootstraps = FIXED_METTA_BOOTSTRAPS + additional_metta_bootstraps
    environment = Environment(
        name=name,
        config=config,
        bootstraps=metta_bootstraps,
        config_label=load_more_from_label,
        config_base=load_more_from_base)
    return add_environment(name, environment)


def new_environments_from_config(
        config: Config, additional_metta_bootstraps: List[str] = DEFAULT_ADDITIONAL_METTA_BOOTSTRAPS, label: str = METTA_PLUGIN_CONFIG_LABEL_ENVIRONMENTS, base: str = LOADED_KEY_ROOT):
    """ Create new environments from config

    Ask the passed config object for information about environments.  From that
    information we create an environment objects.

    Parameters:
    -----------

    config (Config) : config source used to discover environments to create, and
        passed to environments objects for construction

    additional_metta_bootstraps (List[str]) : run additiional metta bootstraps
        on the config object.  Defaults to the metta bootstrap.

    additional_configerus_bootstraps (List[str]) : run additional configerus
        bootstrap entry_points

    """
    logger.info(
        "Discovering environments from config: {}:{}".format(
            label, base))

    # Build any environment describe in config (in all of the metta.yml files)
    environments_config = config.load(label)
    if environments_config is not None:
        environments_dict = environments_config.get(base)
        if environments_dict is not None:
            metta_bootstraps = FIXED_METTA_BOOTSTRAPS + additional_metta_bootstraps
            for name in environments_dict.keys():
                environment_base = [base, name]
                logger.debug(
                    "creating new environment from config: {}:{}".format(
                        label, environment_base))
                environment = Environment(
                    name=name,
                    config=config,
                    bootstraps=metta_bootstraps,
                    config_label=label,
                    config_base=environment_base)
                add_environment(name, environment)


def new_environment_from_config(config: Config, name: str = DEFAULT_ENVIRONMENT_NAME,
                                additional_metta_bootstraps: List[str] = DEFAULT_ADDITIONAL_METTA_BOOTSTRAPS,
                                load_more_from_label: str = '', load_more_from_base: str = LOADED_KEY_ROOT):
    """ Make a new environment from an existing configerus.Config object

    Use a passed configerus Config object to create an environment object,
    register the env and then return it.

    The config object is bootstrapped before we create the environment.

    Parameters
    ----------

    config (Config) : passed to the environment for construction

    additional_metta_bootstraps (List[str]) : run additiional metta bootstraps
        on the config object.  Defaults to the metta bootstrap.

    additional_configerus_bootstraps (List[str]) : run additional configerus
        bootstrap entry_points

    Returns:
    --------

    An intialized Environment object from the config

    """
    bootstraps = FIXED_METTA_BOOTSTRAPS + additional_metta_bootstraps
    environment = Environment(
        name=name,
        config=config,
        bootstraps=bootstraps,
        config_label=load_more_from_label,
        config_base=load_more_from_base)
    return add_environment(name, environment)


def new_environments_from_builder(
        config: Config, additional_metta_bootstraps: List[str], module: str, method: str):
    """ Create environments using an external environment builder option

    This method will import and call a method to build environments dynamically.

    This is usefull in cases where building environments from flat config is not
    possible due to complexity, or if it would be overly redundant.

    This method receives a python package/module name which it imports.  Then the
    method of that imported package is executed and given the Config parameter.
    The method is expected to operate independently, using metta functions to
    register any environments it creates.

    A common approach for this is to use a builder to build dynamic sets of
    configuration from simpler sources, and then use the other new_environment
    methods to process that config.

    Parameters:
    -----------

    config (Config) : base config object which can be used as a base for any new
        environment objects, but can also be used as the source of configuration
        for helping the builder to decide what environments to make.

    additional_metta_bootstraps (List[str]) : metta bootstraps to include on any
        built environment.  This doesn't really make sense, but it is a part
        of the building paradigm so it made sense to included it here.

    module (string) : Python module containing the builder.  This will be
        imported.

    method (string) : Python method which will create the environments.

    """
    try:
        module = importlib.import_module(module)
    except Exception as e:
        raise ValueError(
            "Env builder could not load suggested python package: {}".format(e)) from e

    try:
        method = getattr(module, method)
    except Exception as e:
        raise ValueError(
            "Env builder could not execute package method: {}".format(e)) from e

    method(config, additional_metta_bootstraps)


def environment_names() -> List[str]:
    """ Return a list of all of the created environments """
    return list(_environments)


def has_environment(name: str) -> bool:
    """ Does an environment already exist with a passed name """
    return name in _environments.keys()


def get_environment(name: str = '') -> Environment:
    """ Return an environment that has already been created """
    try:
        if name == '':
            name = list(_environments.keys())[0]
        return _environments[name]
    except KeyError as e:
        raise KeyError(
            "Requested environment has not yet been created: {}".format(name)) from e


def add_environment(name: str, environment: Environment):
    """ Add an environment to the global list """
    global _environments
    if name in _environments:
        logger.warn(
            "Existing environment '{}' is being overwritten".format(name))
    _environments[name] = environment
    return environment
