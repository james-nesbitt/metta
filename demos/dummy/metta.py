"""

METTA Initialization.

This module is discovered by the METTA CLI and used to integrate into the CLI,
primarily by providing fixtures.


"""

from mirantis.testing.metta import new_environment


ENVIRONMENT_NAME = 'dummies'
""" give an arbitrary name to this environment """

# This does a lot of magic, potentially too much.  We use this because we
# found that we had the same configerus building approach on a lot of test
# suites, so we put it all in a common place.
# The important thing it does here is that metta_common tells configerus to
# include ./config as a source of configuration files.
environment = new_environment(name=ENVIRONMENT_NAME, additional_metta_bootstraps=[
    'metta_common_config',
    'metta_dummy'
])
""" common metta environment """

# Tell METTA to look in the fixtures.yml file (configerus source) for
# any fixtures defined there that should be added to the environment.
# This doesn't pass a lot of arguments because we are using it's defaults.
# We will get an exception if there is not fixtures file.
environment.add_fixtures_from_config(exception_if_missing=True)
