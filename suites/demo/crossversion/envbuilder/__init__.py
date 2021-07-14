"""

EnvBuilder environment config builder.

Custom module for building metta environment configuration that will produce
multiple environment objects using a shorter, easier to use format, with
less repetition.

The build() method is used in our conftest as a part of environment discovery.

"""
import copy
from typing import Any, List
import logging

from configerus.config import Config
from configerus.contrib.dict import PLUGIN_ID_SOURCE_DICT

from mirantis.testing import metta

logger = logging.getLogger("env-builder")

STATE_CONFIG_TEMPLATE = {
    "config": {
        "sources": {
            "state_spec": {
                # Include the env specific path as a config source for this
                # environment
                "plugin_id": "dict",
                "priority": 82,
                "data": {},
            }
        }
    }
}
""" this template will be mixed with a varation state to produce env state """


def build(config: Config, additional_metta_bootstraps: List[str]):
    """Build environments for the cross version testing.

    What we do here is to take the custom format of the envbuilder yml and convert
    it into the environments.yml equivalent in memory.  Then we use that single
    environments yaml as a config source for building environments.

    This allows us to keep all of the advantages of the full format, without
    having to write a lot of code.
    We could create one environment config per target, but then we would be
    adding a lot of config sources which is its own verbosity issue.

    """
    envconf = config.load("envbuilder")
    """ all envbuilder config """

    env_common = envconf.get("base")

    environments = {}

    logger.debug("VARIATIONS --> %s", envconf.get("variations"))

    for variation in envconf.get("variations").keys():
        variation = str(variation)  # avoid use of numbers
        var_base = ["variations", variation]
        """ config base that gives us the root of the variation in config """

        config_common = envconf.get([var_base, "common"], default={})

        states = {}
        default_state = None
        for state in envconf.get([var_base, "states"]).keys():
            if default_state is None:
                default_state = state

            state_conf = envconf.get([var_base, "states", state])
            combined_config = tree_merge(
                copy.deepcopy(config_common), copy.deepcopy(state_conf)
            )

            states[state] = copy.deepcopy(STATE_CONFIG_TEMPLATE)
            states[state]["config"]["sources"]["state_spec"]["data"] = combined_config

        environments[variation] = copy.deepcopy(env_common)
        environments[variation]["states"] = {
            "default": default_state,
            "available": states,
        }

        # raise ValueError(f"{variation}-common: {json.dumps(config_common, indent=2)}")
        # raise ValueError(f"{variation}: {json.dumps(environments[variation], indent=2)}")

    # Add our constructed environments list as a config source
    config.add_source(
        plugin_id=PLUGIN_ID_SOURCE_DICT, instance_id="env-builder"
    ).set_data({"environments": environments})

    metta.new_environments_from_config(
        config=config,
        additional_metta_bootstraps=additional_metta_bootstraps,
        label="environments",
    )


# @TODO replace this with https://github.com/toumorokoshi/deepmerge ?
def tree_merge(source: Any, destination: Any):
    """Deep merge source into destination."""
    if not (isinstance(source, dict) and isinstance(destination, dict)):
        return source

    for key, value in source.items():
        if isinstance(value, dict) and key in destination:
            value = tree_merge(value, destination[key])
        destination[key] = value

    return destination
