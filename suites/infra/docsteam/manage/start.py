"""

Start the Docs team investigation service.

Start the infrastructure that can be used by the docs team for discovery
and investigation.

"""
import logging

from mirantis.testing.metta import discover, get_environment
from mirantis.testing.metta.provisioner import METTA_PLUGIN_TYPE_PROVISIONER

logger = logging.getLogger('docsteam-infra')


def main():
    """Run main entrypoint."""
    # Tell metta to scan for automatic configuration of itself.
    # It starts my looking in paths upwards for a 'metta.yml' file; if it finds
    # one then it uses that path as a root source of config
    discover()

    env = get_environment()
    prov_fixture = env.fixtures.get(plugin_type=METTA_PLUGIN_TYPE_PROVISIONER)
    prov_plugin = prov_fixture.plugin

    logger.info("Starting DocsTeam infrastructure")
    prov_plugin.prepare()
    prov_plugin.apply()


if __name__ == '__main__':
    main()
