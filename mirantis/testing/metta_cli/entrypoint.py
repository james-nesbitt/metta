"""

METTA CLI setuptools entrypoint

Keep the entrypint minimal, and rely on .base for real work.

"""

import logging

import fire

from .root import Root

logger = logging.getLogger("metta.cli.entrypoint")


def main():
    """Main entrypoint"""
    fire.Fire(Root)


if __name__ == "__main__":
    main()
