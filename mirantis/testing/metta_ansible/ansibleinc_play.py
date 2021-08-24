"""

Ansible Playbook client.

This module centralizes the ansible integration for metta, to be used by
various plugins for the package.  The client expects to run playbook style
queues, receiving task instructions in collection/primitive form.

"""

from typing import Dict, Any
import logging

import ansible.constants as C
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.inventory.manager import InventoryManager
from ansible.parsing.dataloader import DataLoader
from ansible.playbook.play import Play
from ansible.plugins.callback import CallbackBase
from ansible.vars.manager import VariableManager
from ansible.utils.context_objects import CLIArgs
from ansible import context

from .ansible_callback import ResultsCallback

logger = logging.getLogger("ansible")


class AnsiblePlay:
    """

    Ansible integration class.

    Allows execution of ansible commands using the ansible core directl.

    """

    def __init__(self, inventory_path: str, ansiblecfg_path: str = None):
        """Initial configuration of ansible plugin."""
        self.inventory_path: str = inventory_path
        """Path to the ansible inventory file."""

        # We should pass these in.
        self._passwords: Dict[str, str] = {}
        """Passwords that should be passed to the ansible queue exec."""

        # We should pass these in as args to the constructor
        # WE will likely want to add modules/libraries here.
        cliargs = {"connection": "smart", "verbosity": 10}

        # things we should add to the cliargs dict:
        # - module_path=[] : string paths that should provide ansible python modules
        # - check=False : I don't know what this does.
        # - diff=False : I think ansible outputs more cached diff stuff
        # Things we probably don't need:
        # - become_user=None / become_method=None : sudo kind of stuff.
        # - forks=10 : how many threads to run

        context.CLIARGS = CLIArgs(cliargs)

        if ansiblecfg_path:
            C.config._config_file = ansiblecfg_path
            C.config.update_config_data()
            logger.warning(
                "NOW OVER HERE: %s", C.config.get_config_value_and_origin("COLLECTIONS_PATHS")
            )

    def ping(self, hosts: Any = "all", gather_facts: bool = False) -> ResultsCallback:
        """Ping all hosts in the inventory."""
        # create data structure that represents our play, including tasks,
        # this is basically what our YAML loader does internally.
        play = dict(
            name="Hosts ping",
            hosts=hosts,
            gather_facts="yes" if gather_facts else "no",
            tasks=[
                dict(action=dict(module="ping")),
            ],
        )

        # Instantiate our custom callback for handling results as they come in.
        # Ansible expects this to be one of its main display outlets
        results_callback = ResultsCallback()

        self.play(play, callback=results_callback)
        return results_callback

    def debug(self, hosts: Any = "all", gather_facts: bool = False) -> ResultsCallback:
        """Debug all hosts in the inventory."""
        # create data structure that represents our play, including tasks,
        # this is basically what our YAML loader does internally.
        play = dict(
            name="Hosts ping",
            hosts=hosts,
            gather_facts="yes" if gather_facts else "no",
            tasks=[
                dict(action=dict(module="debug")),
            ],
        )

        # Instantiate our custom callback for handling results as they come in.
        # Ansible expects this to be one of its main display outlets
        results_callback = ResultsCallback()

        self.play(play, callback=results_callback)
        return results_callback

    def setup(self, hosts: Any = "all", gather_facts: bool = False) -> ResultsCallback:
        """Retrieve setup info from all hosts in the inventory."""
        play = dict(
            name="Hosts setup",
            hosts=hosts,
            gather_facts="yes" if gather_facts else "no",
            tasks=[
                dict(action=dict(module="setup")),
            ],
        )

        # Instantiate our custom callback for handling results as they come in.
        # Ansible expects this to be one of its main display outlets
        results_callback = ResultsCallback()

        self.play(play, callback=results_callback)
        return results_callback

    # ansible contants are not all defined before using.
    # pylint: disable=no-member
    def play(
        self,
        play: Dict[str, Any],
        callback: CallbackBase = C.DEFAULT_STDOUT_CALLBACK,
        variables: Dict[str, str] = None,
    ) -> int:
        """Run a playbook in a queue defined as a dict.

        Parameters:
        -----------
        play: dict representation of a yaml playbook file
        callback: callback option. If you want real data out of the callbacks then pass in an
            object which can capture the data.
            You can use this to send a custom object that you intend to use to retrieve results.

            @NOTE this looks like the wrong approach.  We should probably ensure that a custom
                callback is always included in the callback set and then always return it.

        Returns:
        --------
        Integer QueueManager result code

        """
        # initialize needed objects

        # Takes care of finding and reading yaml, json and ini files.
        loader = DataLoader()
        # Will handle our host/inventories.
        inventory = InventoryManager(loader=loader, sources=[self.inventory_path])
        # takes care of merging all the different sources to give you unified view of variable
        variable_manager = VariableManager(loader=loader, inventory=inventory)

        # instantiate task queue manager, which takes care of forking and setting up all objects to
        # iterate over host list and tasks
        # IMPORTANT: This also adds library dirs paths to the module loader
        # IMPORTANT: and so it must be initialized before calling `Play.load()`.
        tqm = TaskQueueManager(
            inventory=inventory,
            variable_manager=variable_manager,
            loader=loader,
            passwords=self._passwords,
            stdout_callback=callback,
        )

        # Create play object, playbook objects use .load instead of init or new methods,
        # this will also automatically create the task objects from info provided in play_source
        play_instance = Play().load(
            play,
            variable_manager=variable_manager,
            loader=loader,
            vars=variables if variables else {},
        )

        # Actually run it
        try:
            results = tqm.run(
                play_instance
            )  # most interesting data for a play is actually sent to the callback's methods
        finally:
            # we always need to cleanup child procs and the structures we use to communicate with
            tqm.cleanup()
            if loader:
                loader.cleanup_all_tmp_files()

        return results
