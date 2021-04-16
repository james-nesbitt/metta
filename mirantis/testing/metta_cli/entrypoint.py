"""

METTA CLI setuptools entrypoint

Keep the entrypint minimal, and rely on .base for real work.

"""

import logging

import fire

from .base import Base

logger = logging.getLogger('metta.cli.entrypoint')


def main():
    """ Main entrypoint """
    fire.Fire(Base)


if __name__ == '__main__':
    main()
