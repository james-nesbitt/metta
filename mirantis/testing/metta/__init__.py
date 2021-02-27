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
import importlib.util

from configerus import new_config as configerus_new_config
from configerus.config import Config

from .discover import discover_metta_from_config, discover_project_config
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
    "metta_common"
]
DEFAULT_ADDITIONAL_METTA_BOOTSTRAPS = [
    "metta_ansible",
    "metta_docker",
    "metta_dummy",
    "metta_kubernetes",
    "metta_terraform"
]
""" default overridable metta bootstrap calls """

DEFAULT_ENVIRONMENT_NAME = 'default'
""" If you don't ask for a particular environment, you are going to get this one """

CWD = os.path.realpath(os.getcwd())
""" CWD if needed """

""" Environments """

_environments = {}
""" Keep a Dict of all created environments for introspection """


def new_environments_from_discover(path: str = CWD, additional_metta_bootstraps: List[str] = DEFAULT_ADDITIONAL_METTA_BOOTSTRAPS,
                                   additional_configerus_bootstraps: List[str] = []):
    """ Discover environments by looking for configuration

    We start of by scanning the path, and all of its parents for a metta.yml
    file.  We collect all of the paths as config sources, into a config object.

    We ask that object for information about required python imports to allow
    local code to be imported.  this is often to allow plugin registration.

    Then we ask that config object for information about environments.  From that
    information we create an environment object.
    Environment objects will receive a copy of the config object, and may also
    have more sources added.

    Parameters:
    -----------

    path (str) : we will be scanning path/parents looking for some configuration
      for meta.  With this argument you can suggest the starting poing for the
      scan.

    """
    logger.debug("Discovering project from path {}".format(path))
    configerus_bootstraps = FIXED_CONFIGERUS_BOOSTRAPS + \
        additional_configerus_bootstraps
    project_config = configerus_new_config(bootstraps=configerus_bootstraps)

    discover_project_config(project_config, path)
    discover_metta_from_config(project_config)
    metta_config = project_config.load('metta')

    imports_config = metta_config.get('imports')
    if imports_config is not None:
        for import_name in imports_config:
            module_path = metta_config.get(['imports', import_name, 'path'])
            if os.path.isdir(module_path):
                if path not in sys.path:
                    sys.path.append(path)
            elif os.path.isfile(module_path):
                spec = importlib.util.spec_from_file_location(
                    import_name, module_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                logger.debug(
                    "Loaded module: {} : {}".format(
                        import_name, module_path))

    environments_config = metta_config.get('environments')
    if environments_config is not None:
        for environment_name in environments_config.keys():
            environment_config = project_config.copy()
            """ use a copy of the config for each environment so that they can diverge """
            environment_metta_config = project_config.load('metta')
            environment_base = ['environments', environment_name]

            config_sources = environment_metta_config.get(
                [environment_base, 'config.sources'])
            if config_sources is not None:
                for instance_id in config_sources.keys():
                    instance_base = [
                        environment_base, 'config.sources', instance_id]
                    plugin_id = environment_metta_config.get(
                        [instance_base, 'plugin_id'], exception_if_missing=True)
                    priority = environment_metta_config.get(
                        [instance_base, 'priority'], exception_if_missing=False)
                    if priority is None:
                        priority = DEFAULT_SOURCE_PRIORITY

                    logger.debug(
                        "Adding metta sourced config plugin to environment: {}:{}".format(
                            plugin_id, instance_id))
                    plugin = environment_config.add_source(
                        plugin_id=plugin_id, instance_id=instance_id, priority=priority)

                    if plugin_id == 'path':
                        path = environment_metta_config.get(
                            [instance_base, 'path'], exception_if_missing=True)
                        plugin.set_path(path=path)
                    elif plugin_id == 'dict':
                        data = environment_metta_config.get(
                            [instance_base, 'data'], exception_if_missing=True)
                        plugin.set_data(data=data)

            # Check to see if we should pass any bootstraps to the environment
            # factory.
            metta_bootstraps = environment_metta_config.get(
                ['environments', environment_name, 'bootstraps.metta'])
            if metta_bootstraps is None:
                metta_bootstraps = DEFAULT_ADDITIONAL_METTA_BOOTSTRAPS

            new_env = new_environment_from_config(
                config=environment_config,
                name=environment_name,
                additional_metta_bootstraps=metta_bootstraps)

            metta_fixtures = environment_metta_config.get(
                ['environments', environment_name, 'fixtures'])
            if metta_fixtures is not None:
                metta_fixtures_from_config = environment_metta_config.get(
                    ['environments', environment_name, 'fixtures', 'from_config'])
                if metta_fixtures_from_config is None:
                    pass
                elif isinstance(metta_fixtures_from_config, dict):
                    label = metta_fixtures_from_config['label'] if 'label' in metta_fixtures_from_config else 'metta'
                    base = metta_fixtures_from_config['base'] if 'base' in metta_fixtures_from_config else ''
                    new_env.add_fixtures_from_config(
                        label=label, base=base, exception_if_missing=True)


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

    environment = Environment(name=name, config=config)

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


def get_environment(name: str = '') -> Environment:
    """ Return an environment that has already been created """
    try:
        if name == '':
            name = list(_environments.keys())[0]
        return _environments[name]
    except KeyError as e:
        raise KeyError(
            "Requested environment has not yet been created: {}".format(name)) from e
