"""

k0sctl command line executor.

"""
from typing import Dict, Any


class K0sctl:
    """

    k0sctl cli command executor.

    """

    # deep is a metta info standard and expected to be here
    # pylint: disable=unused-argument
    def info(self, deep: bool = False) -> Dict[str, Any]:
        """Provide a Dict of info about the client."""
        return {}
