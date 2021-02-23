"""

MTT Mirantis


"""

from typing import List
import os

from uctt import bootstrap as uctt_bootstrap
from uctt.environment import Environment

from .common import add_common_config
from .presets import add_preset_config

""" UCTT BOOTSTRAPPERS """

""" UCTT bootstraps that we will use on config objects """


def uctt_bootstrap_all(environment: Environment):
    """ MTT configerus bootstrap

    Add some Mirantis specific config options

    run bootstrapping for both common and presets

    """
    uctt_bootstrap_common(environment)
    uctt_bootstrap_presets(environment)


""" UCTT bootstraps that we will use on config objects """


def uctt_bootstrap_common(environment: Environment):
    """ MTT configerus bootstrap

    Add some common Mirantis specific config options

    Add some common configerus sources for common data and common config source
    paths. Some of the added config is dynamic interpretation of environment,
    while also some default config paths are added if they can be interpeted

    @see .config.add_common_config() for details

    """
    add_common_config(environment)


""" UCTT bootstraps that we will use on config objects """


def uctt_bootstrap_presets(environment: Environment):
    """ MTT configerus bootstrap

    Add some Mirantis specific config options for presets

    Additional config sources may be added based on config.load("mtt")
    which will try to add config for mtt `presets`
    This gives access to "variation", "cluster", "platform" and "release"
    presets.  You can dig deeper, but it might implicitly make sense if you look
    at the config folder of this module.

    @see .presets.add_preset_config() for details

    """
    add_preset_config(environment)
