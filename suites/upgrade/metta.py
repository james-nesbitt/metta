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
from mirantis.testing.metta import new_environment

import mirantis.testing.metta_launchpad

ENVIRONMENT_NAME = 'sanity'
""" What to call our METTA Environment """

""" Create and return the common environment. """
environment = new_environment(name=ENVIRONMENT_NAME, additional_metta_bootstraps=[
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

# Tell METTA to look in the fixtures.yml file (configerus source) for
# any fixtures defined there that should be added to the environment.
environment.add_fixtures_from_config()
