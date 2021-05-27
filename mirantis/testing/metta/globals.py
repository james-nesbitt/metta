"""

Global mutables.

Keep all package global variables in this module.

"""
from typing import Dict

from mirantis.testing.metta.environment import Environment

all_environments: Dict[str, Environment] = {}
""" Keep a Dict of all created environments for introspection """
