"""

Test that some clients work

"""

import logging

from mirantis.testing.metta.workload import METTA_PLUGIN_TYPE_WORKLOAD

logger = logging.getLogger("test_mirantis_clients")


def test_01_docker_run_workload(environment_up, benchmark):
    """ test that we can run a docker run workload """

    # we have a docker run workload fixture called "sanity_docker_run"
    sanity_docker_run = environment_up.fixtures.get_plugin(plugin_type=METTA_PLUGIN_TYPE_WORKLOAD,
                                                           instance_id='sanity_docker_run')
    """ workload plugin """
    def container_run():
        try:
            docker_run_instance = sanity_docker_run.create_instance(environment_up.fixtures)
            run_output = docker_run_instance.apply()
            assert 'Hello from Docker' in run_output.decode("utf-8")
        except Exception as err:
            raise RuntimeError("Docker run failed") from err

    # benchmark will run the container_run function a number of times and benchmark it.
    benchmark(container_run)
