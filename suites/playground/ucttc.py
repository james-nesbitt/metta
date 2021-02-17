"""

UCTT CLI integration

This module is discovered by the UCTT CLI and used to integrate into the CLI,
primarily by providing fixtures.
This file is not intended for use outside of UCTTC (the cli for UCTTC) but
it doesn't break anything.

The following fixtures are kind of needed to gain awareness of your project:

'provisioner': a configured provisioner

"""
from uctt import new_environment


ENVIRONMENT_NAME = 'playground'
""" What to call our UCTT Environment """

""" Create and return the common environment. """
environment = new_environment(name=ENVIRONMENT_NAME, additional_uctt_bootstraps=[
    'uctt_docker',
    'uctt_kubernetes',
    'uctt_terraform',
    'mtt',
    'mtt_launchpad'
])
# This does a lot of magic, potentially too much.  We use this because we
# found that we had the same configerus building approach on a lot of test
# suites, so we put it all in a common place.

# Tell UCTT to look in the fixtures.yml file (configerus source) for
# any fixtures defined there that should be added to the environment.
environment.add_fixtures_from_config()
