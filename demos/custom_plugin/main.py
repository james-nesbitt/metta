
from mirantis.testing.metta import get_environment
from mirantis.testing.metta.plugin import Type

# Import the metta environment constructor which creates an environment.
from metta import ENVIRONMENT_NAME


def main():
    """ Main entrypoint """

    env = get_environment(ENVIRONMENT_NAME)
    my_client = env.fixtures.get_plugin(
        type=Type.CLIENT, plugin_id="my_client")

    while len(my_client):
        print(my_client.get_message())


if __name__ == '__main__':
    main()
