"""

METTA CLI integration

This module is discovered by the METTA CLI and used to integrate into the CLI,
primarily by providing fixtures.
This file is not intended for use outside of METTA (the cli for METTA) but
it doesn't break anything.

The following fixtures are kind of needed to gain awareness of your project:

'config': a sourced configerus Config object.  If you don't pass this fixture
    then an empty config is created.

The following are optional but a good idea

'provisioner': a configured provisioner

"""
import os.path
from typing import List

from configerus.contrib.files import PLUGIN_ID_SOURCE_PATH

from mirantis.testing.metta import new_environment, get_environment
from mirantis.testing.metta import Environment

import mirantis.testing.metta_launchpad

ENVIRONMENT_NAME = 'upgrade'
""" Base name for all of the METTA Environment """
ENVIRONMENT_PHASES = [
    'before',
    'after'
]
""" Each phase will be its own environment """


class EnvironmentPhases:

    def __init__(self, phases: List[str], base_name: str = ENVIRONMENT_NAME):
        """

        Parameters:
        -----------

        phases (List[str]) : ordered string list of environment names to be
            used in sequence

        """
        self.phases = []

        for phase in phases:
            environment_name = "{}-{}".format(base_name, phase)

            """ Create and return the common environment. """
            environment = new_environment(name=environment_name, additional_metta_bootstraps=[
                'metta_common',
                'metta_ansible',
                'metta_docker',
                'metta_kubernetes',
                'metta_terraform',
                'metta_launchpad',
                'metta_common_config',
                'metta_mirantis_common',
                'metta_mirantis_presets'
            ])
            # This does a lot of magic, potentially too much.  We use this because we
            # found that we had the same configerus building approach on a lot of test
            # suites, so we put it all in a common place.

            phase_config_path = os.path.join(
                environment.config.format(
                    '{paths:project_config}',
                    default_label='paths'),
                'phase',
                phase)
            if os.path.isdir(phase_config_path):
                environment.config.add_source(plugin_id=PLUGIN_ID_SOURCE_PATH, instance_id=environment_name,
                                              priority=environment.config.default_priority() + 10
                                              ).set_path(phase_config_path)
            else:
                raise ValueError(
                    "Phase {} had no environment config path: {}".format(
                        phase, phase_config_path))

            # Tell METTA to look in the fixtures.yml file (configerus source) for
            # any fixtures defined there that should be added to the
            # environment.
            environment.add_fixtures_from_config()

            self.phases.append(environment_name)

        self.index = 0

    def current(self) -> Environment:
        """ get the current environment object """
        return get_environment(self.phases[0])

    def next(self) -> bool:
        """ move to the next environment

        Returns
        -------

        Bool whether or not there was a next phase

        """
        self.index += 1
        return self.index >= len(phases)


PHASES = EnvironmentPhases(
    phases=ENVIRONMENT_PHASES,
    base_name=ENVIRONMENT_NAME)
""" Exported Environment Phases object """
