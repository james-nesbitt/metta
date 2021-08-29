"""

Bootstrapping Metta when it starts to run.

Separate abstraction for boostrapping python modules by executing setuptools
entrypoints with arbitrary arguments.

"""
import logging
from typing import List, Dict, Any
import os

from configerus.config import Config

from .plugin import Factory
from .fixture import Fixture
from .globals import global_fixtures
from .building import FixtureBuildingFromConfigMixin, FixtureBuildingFromDictMixin
from .discover import discover_project_root
from .config import add_config_sources_from_config, METTA_CONFIG_CONFIG_SOURCE_KEY
from .importing import add_imports_from_config, METTA_IMPORT_CONFIG_LABEL
from .setuptools import setuptools_entrypoint, METTA_CONFIG_SETUPTOOLS_BOOTSTRAPS_KEY
from .environment import METTA_FIXTURES_CONFIG_ENVIRONMENTS_KEY

logger = logging.getLogger("metta.bootstrapper")

METTA_ENTRYPOINT_BOOTSTRAPPER = "metta.bootstrap.bootstrapper"
""" SetupTools entry_point used for METTA bootstrapping bootstrappers """

METTA_PLUGIN_INTERFACE_ROLE_BOOTSTRAPPER = "bootstrapper"
""" metta plugin interface identifier for environment plugins """

METTA_BOOTSTRAPPER_CORE_PLUGIN_ID = "core_bootstrap"
"""A core default bootstrapper."""
METTA_BOOTSTRAPPER_PROJECT_PLUGIN_ID = "project_bootstrap"
"""A core default bootstrapper."""

METTA_BOOTSTRAP_PROJECT_CONFIG_LABEL = "metta"
"""Configerus .load() label for finding project bootstrapping config."""

CWD = os.path.realpath(os.getcwd())
""" CWD if needed for project discovery """


@Factory(
    plugin_id=METTA_BOOTSTRAPPER_CORE_PLUGIN_ID,
    interfaces=[METTA_PLUGIN_INTERFACE_ROLE_BOOTSTRAPPER],
)
def core_bootstrap(config: Config, instance_id: str) -> "BootStrapFixtureBuilder":
    """Core default bootstrapper.

    This bootstrapper works by assuming that enough config is in place for it to
    be able to create environments, and that those environments know how to
    create any fixtures excepted based on their config.
    This sounds elegant, but of course it means that the user needs to know how
    to write config in the right way. At least the config is very standardized
    and repeated, so all you really need to know is:

    1. there should be config under the label "metta".
    2. that config can optionally direct us to include more config
    3. that config can optionally direct us to import some python (which is good
        for importing modules that contain plugins.)
    4. that config should probable container an "environments" base which is an
        array of config objects that define environment plugin instances.
    5. Those environments can also repeat #2 and #3 above,
    6 Those environments should probably contain "fixture" bases as arrays of
        plugins that we should create.

    """
    # 1. add any config sources specified in config
    # (Here config tells us to load more config. It is weird but ok.)
    add_config_sources_from_config(
        config=config,
        label=METTA_BOOTSTRAP_PROJECT_CONFIG_LABEL,
        base=METTA_CONFIG_CONFIG_SOURCE_KEY,
    )

    # 2. import any python code requested, to make sure that all funxtionality
    #    is in scope that is needed.
    #    Here we say look in the "metta" config for a "imports" section.
    add_imports_from_config(
        config=config, label=METTA_BOOTSTRAP_PROJECT_CONFIG_LABEL, base=METTA_IMPORT_CONFIG_LABEL
    )

    # create a bootstrap builder which will build plugins in global scope
    builder: BootStrapFixtureBuilder = BootStrapFixtureBuilder(
        config=config, instance_id=instance_id
    )

    # 3. run any bootstrapper setuptools bootstraps
    bootstrapper_bootstraps: List[str] = config.load(METTA_BOOTSTRAP_PROJECT_CONFIG_LABEL).get(
        METTA_CONFIG_SETUPTOOLS_BOOTSTRAPS_KEY, default=[]
    )
    setuptools_entrypoint(
        entrypoint=METTA_ENTRYPOINT_BOOTSTRAPPER,
        entries=bootstrapper_bootstraps,
        args=[builder],
        kwargs={},
    )

    # 4. build environments from config
    #    Environment plugins are top level containers, and should build their
    #    own plugins on creation.
    try:
        labels: Dict[str, str] = {
            "container": "bootstrapper",
            "container_id": instance_id,
            "bootstrapper": instance_id,
        }
        builder.add_fixtures_from_config(
            label=METTA_BOOTSTRAP_PROJECT_CONFIG_LABEL,
            base=METTA_FIXTURES_CONFIG_ENVIRONMENTS_KEY,
            labels=labels,
            exception_if_missing=True,
        )
    except KeyError as err:
        raise RuntimeError(
            f"Bootstrapper encountered an issue creating environments from config: {err}"
        ) from err

    return builder


@Factory(
    plugin_id=METTA_BOOTSTRAPPER_PROJECT_PLUGIN_ID,
    interfaces=[METTA_PLUGIN_INTERFACE_ROLE_BOOTSTRAPPER],
)
def project_bootstrap(
    config: Config, instance_id: str, path: str = CWD
) -> "BootStrapFixtureBuilder":
    """Bootstrap Metta by looking in a file-system for a project.

    First we look in the file system for some config files, and use that
    file path and config as a source of direction on how to bootstrap Metta.

    That file source can be like any fixture building config in that it can
    instructions for importing python modules, describing config sources,
    and building fixtures, but any plugins that required an environment may
    fail as the fixture builder does not pass in an Environment.

    Parameters:
    -----------
    config (Config) : Configerus Config object used internally and by any
        functionality that wants to consider itself inside the environment.

    """
    # 1. Discover a root project config path, which gives us enough config to start
    discover_project_root(config, start_path=path)

    # At this point, the setup is done as we should have found some standardized
    # config which instructs the core bootloader how to do its magic.
    # @see core_bootstrap above

    # 2. run the core bootstrapper
    instance_id = f"{instance_id}-core"
    args: List[Any] = [config, instance_id]
    kwargs: Dict[str, Any] = {}
    return Factory.create(METTA_BOOTSTRAPPER_CORE_PLUGIN_ID, instance_id, *args, **kwargs)


class BootStrapFixtureBuilder(FixtureBuildingFromConfigMixin, FixtureBuildingFromDictMixin):
    """A utility tool to build bootstrap fixtures in global scope."""

    def __init__(self, config: Config, instance_id: str):
        """Get a config object.

        Parameters:
        -----------
        config (Config) : Configerus Config object used internally and by any
            functionality that wants to consider itself inside the environment.

        """
        self._config = config
        """Keep the config object in scope for fixture building."""
        self._instance_id: str = instance_id
        """Use this builder name for reporting."""

        FixtureBuildingFromConfigMixin.__init__(
            self, config=config, builder_callback=self.new_fixture
        )
        FixtureBuildingFromDictMixin.__init__(self, builder_callback=self.new_fixture)

    # This is what it takes to build a plugin
    # pylint: disable=too-many-arguments
    def new_fixture(
        self,
        plugin_id: str,
        instance_id: str,
        priority: int,
        arguments: Dict[str, Any] = None,
        labels: Dict[str, Any] = None,
        replace_existing=False,
    ) -> Fixture:
        """Create a new global plugin from parameters.

        Parameters:
        -----------
        plugin_id (str) : METTA plugin id to tell us what plugin factory to use;

            @see .plugin.Factory for more details on how plugins are loaded.

        instance_id (str) : string instance id that will be passed to the new
            plugin object;

        priority (int) : Integer priority 1-100 for comparative prioritization
            between other plugins;

        arguments (Dict[str, Any]) : Keyword Arguments which should be passed to
            the plugin constructor after environment and instance_id;

        labels (Dict[str, str]) : Keyword/value labels which are to be associated
            with the plugin/fixture;

        replace_existing (bool) : Replace any existing matching fixture.

        Return:
        -------
        A Fixture object with the new plugin added

        The Fixtures has already been added to the global fixtures, but is returned
        so that the consumer can act on it separately without haveing to
        search for it.

        Raises:
        -------
        NotImplementedError if you asked for an unregistered plugin_id

        """
        if arguments is None:
            arguments = {}

        # Catch some early arg validation errors which would otherwise have
        # caused some hard to diagnose issues.
        if not (
            isinstance(plugin_id, str)
            and isinstance(instance_id, str)
            and isinstance(priority, int)
        ):
            raise ValueError(
                f"Bad arguments passed for creating a fixture: "
                f":{plugin_id}:{instance_id} ({priority})"
            )

        if labels is None:
            labels = {}
        labels["bootstrapper"] = self._instance_id

        # Build the plugin instance by passing collected arguments to the
        # registered plugin factory. This will call whatever function was
        # decorated for the plugin_id.
        args: List[Any] = [self._config, instance_id]
        kwargs: Dict[str, Any] = arguments
        plugin_instance = Factory.create(plugin_id, instance_id, *args, **kwargs)

        # Build a fixture from the plugin_instance and add it to the fixtures
        # set for the environment, then return the fixture.
        fixture = global_fixtures.add(
            fixture=Fixture.from_instance(plugin_instance, priority=priority, labels=labels),
            replace_existing=replace_existing,
        )
        return fixture
