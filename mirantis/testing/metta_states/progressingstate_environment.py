"""

A state based environment that focuses on progressing across states.

"""

from .state_environment import StateBasedEnvironment


METTA_ENVIRONMENT_STATEPROGRESSING_PLUGIN_ID = "metta_stateprogressing_environment"
""" Metta plugin id for the state-progressing environment plugin."""


class StateProgressingEnvironment(StateBasedEnvironment):
    """A state environment implementation that progressed through states.

    This extension of the state based environment, focuses on the state fixtures
    as a linear set, which is to be progressed through.

    The set-state is never allowed to move backwards in the list, and if asked
    progress past states, it will activate them before moving on.

    """
