import copy
from typing import Any, List
import logging
import json

from configerus.config import Config
from configerus.contrib.dict import PLUGIN_ID_SOURCE_DICT

import mirantis.testing.metta as metta

logger = logging.getLogger('env-builder')

STATE_CONFIG_TEMPLATE = {
    'config': {
        'sources': {
            'state_spec': {
                # Include the env specific path as a config source for this
                # environment
                'plugin_id': 'dict',
                'priority': 82,
                'data': {}
            }
        }
    }
}
""" this template will be mixed with a varation state to produce an env state """


def build(config: Config, additional_metta_bootstraps: List[str]):
    """ Build environments for the cross version testing

    What we do here is to take the custom format of the envbuilder yml and convert
    it into the environments.yml equivalent in memory.  Then we use that single
    environments yaml as a config source for building environments.

    This allows us to keep all of the advantages of the full format, without
    having to write a lot of code.
    We could create one environment config per target, but then we would be
    adding a lot of config sources which is its own verbosity issue.

    """

    envconf = config.load('envbuilder')
    """ all envbuilder config """

    env_common = envconf.get('base', exception_if_missing=True)

    environments = {}

    logger.debug(
        "VARIATIONS --> {}".format(envconf.get('variations', exception_if_missing=True)))

    for variation in envconf.get(
            'variations', exception_if_missing=True).keys():
        variation = str(variation)  # avoid use of numbers
        var_base = ['variations', variation]
        """ config base that gives us the root of the variation in config """

        config_common = envconf.get([var_base, 'common'])
        if config_common is None:
            config_common = {}

        states = {}
        default_state = None
        for state in envconf.get([var_base, 'states'],
                                 exception_if_missing=True).keys():
            if default_state is None:
                default_state = state

            state_conf = envconf.get([var_base, 'states', state])
            combined_config = tree_merge(
                copy.deepcopy(config_common),
                copy.deepcopy(state_conf))

            states[state] = copy.deepcopy(STATE_CONFIG_TEMPLATE)
            states[state]['config']['sources']['state_spec']['data'] = combined_config

        environments[variation] = copy.deepcopy(env_common)
        environments[variation]['states'] = {
            'default': default_state,
            'available': states
        }

    # Add our constructed environments list as a config source
    config.add_source(plugin_id=PLUGIN_ID_SOURCE_DICT, instance_id='env-builder').set_data({
        'environments': environments
    })

    metta.new_environments_from_config(
        config=config,
        additional_metta_bootstraps=additional_metta_bootstraps,
        label='environments')

# @TODO replace this with https://github.com/toumorokoshi/deepmerge ?


def tree_merge(source: Any, destination: Any):
    """
    Deep merge source into destination

    >>> a = { 'first' : { 'all_rows' : { 'pass' : 'dog', 'number' : '1' } } }
    >>> b = { 'first' : { 'all_rows' : { 'fail' : 'cat', 'number' : '5' } } }
    >>> merge(b, a) == { 'first' : { 'all_rows' : { 'pass' : 'dog', 'fail' : 'cat', 'number' : '5' } } }
    True
    """

    if not (isinstance(source, dict) and isinstance(destination, dict)):
        return source

    for key, value in source.items():
        if isinstance(value, dict) and key in destination:
            value = tree_merge(value, destination[key])
        destination[key] = value

    return destination
