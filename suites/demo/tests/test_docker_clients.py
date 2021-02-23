"""

Test that some clients work

"""

import logging

import docker.models.containers
from uctt.contrib.docker import UCTT_PLUGIN_ID_DOCKER_CLIENT

logger = logging.getLogger("test_clients")

container_row_format = "{:<15}{:<15}{:<15}\n"
""" styling formatter for container infomration """


def test_launchpad_docker_client(environment_up, launchpad):
    """ did we get a good docker client ? """

    logger.info("Getting docker client")
    docker_client = launchpad.get_client(
        plugin_id=UCTT_PLUGIN_ID_DOCKER_CLIENT)

    container = docker_client.containers.run(
        "bfirsh/reticulate-splines", detach=True)
    assert container is not None
    print(
        container_row_format.format(
            container.short_id,
            container.image.short_id,
            container.status))

    ps = docker_client.containers.list()
    assert len(
        ps), "No containers were running.  We expected at least the MKE containers"
    assert isinstance(
        ps[0], docker.models.containers.Container), "Did not get a container object from docker list"

    print(
        container_row_format.format(
            container.short_id,
            container.image.short_id,
            container.status) for container in ps)


def test_docker_run_workload(environment_up):
    """ test that we can run a docker run workload """

    # we have a docker run workload fixture called "sanity_docker_run"
    sanity_docker_run = environment_up.fixtures.get_plugin(
        instance_id='sanity_docker_run')
    """ workload plugin """

    sanity_docker_run.set_fixtures(environment_up.fixtures)

    run_output = sanity_docker_run.apply()

    assert 'Hello from Docker' in run_output.decode("utf-8")
