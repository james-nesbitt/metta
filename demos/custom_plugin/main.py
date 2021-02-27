
from mirantis.testing.metta import new_environments_from_discover, get_environment
from mirantis.testing.metta.plugin import Type


def main():
    """ Main entrypoint """

    # Tell metta to scan for automatic configuration of itself.
    # It starts my looking in paths upwards for a 'metta.yml' file; if it finds
    # one then it uses that path as a root source of config
    new_environments_from_discover()

    env = get_environment()
    my_client = env.fixtures.get_plugin(
        type=Type.CLIENT, plugin_id="my_client")

    while len(my_client):
        print(my_client.get_message())


if __name__ == '__main__':
    main()
