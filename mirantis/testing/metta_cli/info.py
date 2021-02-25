import logging
from typing import Dict, Any

from mirantis.testing.metta.cli import CliBase

logger = logging.getLogger('metta.cli.info')


class InfoCliPlugin(CliBase):
    """ metta Cli info plugin

    """

    def fire(self):
        """ return a dict of commands """
        return {
            'info': self.info
        }

    def info(self, raw: bool = True):
        """ return information about the metta cli setup """
        return self._info_raw()

    def _info_raw(self):
        """ return dummy output """
        info = """---  METTA CLI INFO --- \n"""

        info += """-> FIXTURES \n"""

        row_format = "{:<25}{:<20}{:<30}\n"
        info += row_format.format('Type', 'Plugin ID', 'Instance ID')
        for fixture in self.environment.fixtures.get_fixtures().to_list():
            info += row_format.format(fixture.type.value,
                                      fixture.plugin_id, fixture.instance_id)

        return info
