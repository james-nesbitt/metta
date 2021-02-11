"""

UCTT CLI integration

This module is discovered by the UCTT CLI and used to integrate into the CLI,
primarily by providing fixtures.
This file is not intended for use outside of UCTTC (the cli for UCTTC) but
it doesn't break anything.

The following fixtures are kind of needed to gain awareness of your project:

'config': a sourced configerus Config object.  If you don't pass this fixture
    then an empty config is created.

The following are optional but a good idea

'provisioner': a configured provisioner

"""
import fixtures as local_fixtures


def fixtures():
    """ Provide the UCTT cli with fixtures

    config : the config object from ./fixtures
    provsioner : the provisioner object from ./fixtures

    """
    config = local_fixtures.config()
    provisioner = local_fixtures.provisioner(config, instance_id='cli-prov')

    return {
        'config': config,
        'provisioner': provisioner
    }
