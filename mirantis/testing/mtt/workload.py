import logging
from .plugin import MTTPlugin, Type as PluginType, Factory as PluginFactory
from .config import Config

logger = logging.getLogger('mirantis.testing.mtt.workload')

MTT_PLUGIN_ID_WORKLOAD = PluginType.WORKLOAD
""" Fast access to the workload plugin_id """

class WorkloadBase(MTTPlugin):
    """ Base class for workload plugins """

    def arguments(**kwargs):
        """ Receive a list of arguments for this workload """
        raise NotImplemented('arguments() was not implemented for this workload plugin')


def make_workload(plugin_id: str, config: Config, instance_id: str = ''):
    """ Create a new workload plugin

    Parameters:
    -----------

    plugin_id (str) : what workload plugin should be created

    config (Config) : config object to pass to the plugin constructor
    instance_id(str) : instance_id to pass to the plugin constructor

    Returns:
    --------

    A workload plugin instance

    Throws:
    -------

    Can throw a NotImplementedError if you asked for a plugin_id that has not
    been registered.

    """
    logger.debug("Creating workload plugin: %s:%s".format(plugin_id, instance_id))
    workload_factory = PluginFactory(MTT_PLUGIN_ID_WORKLOAD, plugin_id)
    workload = workload_factory.create(config, instance_id)

    if not isinstance(workload, WorkloadBase):
        logger.warn("Created workload plugin does not extend the WorkloadBase")

    return workload
