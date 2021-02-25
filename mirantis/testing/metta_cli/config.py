import logging
from typing import Dict, Any
import json

from configerus.loaded import LOADED_KEY_ROOT
from configerus.plugin import Type as ConfigerusType
from configerus.contrib.files import PLUGIN_ID_SOURCE_PATH
from configerus.contrib.dict import PLUGIN_ID_SOURCE_DICT

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta.cli import CliBase

logger = logging.getLogger('metta.cli.config')


class ConfigCliPlugin(CliBase):

    def fire(self):
        """ return a dict of commands """
        return {
            'config': ConfigGroup(self.environment)
        }


class ConfigGroup():

    def __init__(self, environment: Environment):
        self.environment = environment

    def plugins(self, plugin_id: str = '', instance_id: str = '',
                type: str = ''):
        """ List configerus plugins """
        list = [{
            'type': instance.type.value,
            'plugin_id': instance.plugin_id,
            'instance_id': instance.instance_id,
            'priority': instance.priority,
        } for instance in self.environment.config.plugins.get_instances(plugin_id=plugin_id, instance_id=instance_id, type=type)]

        return json.dumps(list, indent=2)

    def sources(self, plugin_id: str = '',
                instance_id: str = '', deep: bool = False):
        """ List configerus sourceS """
        list = []
        for instance in self.environment.config.plugins.get_instances(
                plugin_id=plugin_id, instance_id=instance_id, type=ConfigerusType.SOURCE):
            source = {
                'type': instance.type.value,
                'plugin_id': instance.plugin_id,
                'instance_id': instance.instance_id,
                'priority': instance.priority,
            }

            if deep:
                if instance.plugin_id == PLUGIN_ID_SOURCE_PATH:
                    source['path'] = instance.plugin.path
                if instance.plugin_id == PLUGIN_ID_SOURCE_DICT:
                    source['data'] = instance.plugin.data

            list.append(source)

        return json.dumps(list, indent=2, default=serialize_last_resort)

    def loaded(self, raw: bool = False):
        """ List loaded config labels """
        loaded = self.environment.config.loaded
        value = list(loaded)
        if raw:
            return value
        else:
            return json.dumps(value)

    def get(self, label: str, key: str = LOADED_KEY_ROOT):
        """ Retrieve configuration from the config object

        USAGE:

            metta config get {label} [{key}]


        """
        try:
            loaded = self.environment.config.load(label)
        except KeyError as e:
            return "Could not find the config label '{}'".format(label)

        try:
            value = loaded.get(key, exception_if_missing=True)
        except KeyError as e:
            return "Could not find the config key '{}'".format(key)

        return json.dumps(value, indent=2, default=serialize_last_resort)

    def format(self, data: str,
               default_label: str = 'you did not specify a default', raw: bool = False):
        """ Format a target string using config templating """

        try:
            value = self.environment.config.format(
                data=data, default_label=default_label)
        except Exception as e:
            return "Error occured in formatting: '{}'".format(e)

        if raw:
            return value
        else:
            return json.dumps(value, indent=2, default=serialize_last_resort)


def serialize_last_resort(X):
    """ last attempt at serializing """
    return "{}".format(X)
