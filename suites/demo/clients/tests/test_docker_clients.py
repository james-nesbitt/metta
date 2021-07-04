"""

Test that some clients work.

Here test the docker run workload.

"""
import logging

import pytest

logger = logging.getLogger("test_clients.docker")


@pytest.fixture(scope="module")
def sanity_docker_run(environment_up):
    """Get the docker run workload from fixtures/yml."""
    # we have a docker run workload fixture called "sanity_docker_run"
    plugin = environment_up.fixtures.get_plugin(instance_id="sanity_docker_run")
    plugin.prepare(environment_up.fixtures)
    return plugin


def test_01_docker_run_workload(sanity_docker_run, benchmark):
    """test that we can run a docker run workload"""

    def container_run():
        try:
            run_output = sanity_docker_run.apply()
            assert "Hello from Docker" in run_output.decode("utf-8")
            sanity_docker_run.destroy()
        except Exception as err:
            raise RuntimeError("Docker run failed") from err

    # benchmark will run the container_run function a number of times and benchmark it.
    benchmark(container_run)
