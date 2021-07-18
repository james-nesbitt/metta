"""

Quick metta demo for injecting custom test-case code into a suite.

"""

from mirantis.testing.metta import discover, get_environment
from mirantis.testing.metta.client import METTA_PLUGIN_TYPE_CLIENT


def main():
    """Main entrypoint."""

    # Tell metta to scan for automatic configuration of itself.
    # It starts my looking in paths upwards for a 'metta.yml' file; if it finds
    # one then it uses that path as a root source of config
    discover()

    env = get_environment()
    fixture = env.fixtures.get(plugin_type=METTA_PLUGIN_TYPE_CLIENT, plugin_id="my_client")
    my_client = fixture.plugin

    while len(my_client):
        print(my_client.get_message())


if __name__ == "__main__":
    main()
