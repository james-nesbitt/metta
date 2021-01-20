
from typing import Dict
from .config import Config
from .provisioner import make_provisioner, ProvisionerBase
from .client import make_client, ClientBase
from .workload import make_workload, WorkloadBase

def new_config():
    """ Retrieve a new empty Config object

    Returns:
    --------

    An empty .config.Config object

    """
    return Config()

MTT_PROVISIONER_CONFIG_LABEL_DEFAULT = 'provisioner'
""" provisioner_from_config will load this config to decide how to build the provisioner plugin """
MTT_PROVISIONER_CONFIG_KEY_PLUGINID = 'plugin_id'
""" provisioner_from_config will .get() this key from the provisioner config to decide what plugin to create """
MTT_PROVISIONER_FROMCONFIG_INSTANCEID_DEFAULT = 'fromconfig'
""" what plugin instance_id to use for the provisioner from config """
def new_provisioner_from_config(
        config: Config,
        instance_id:str=MTT_PROVISIONER_FROMCONFIG_INSTANCEID_DEFAULT,
        config_label:str=MTT_PROVISIONER_CONFIG_LABEL_DEFAULT) -> ProvisionerBase:
    """ Create a new provisioner plugin from a config object

    The config object is used decide what plugin to load.

    First we config.load('provisioner')
    and then we ask for .get('plugin_id')

    Parameters:
    -----------

    config (Config) : used to decide what provisioner plugin to load, and also
        passed to the provisioner plugin

    instance_id (str) : give the provisioner plugins instance a specific name

    config_label (str) : load provisioner config from a specific config label
        This allows you to configure multiple provisioners using a different
        label per provisioner.

    Returns:
    --------

    a provisioner plugin instance created by the decorated factory method that
    was registered for the plugin_id

    Throws:
    -------

    If you ask for a plugin which has not been registered, then you're going to get
    a NotImplementedError exception.
    To make sure that your desired plugin is registered, make sure to import
    the module that contains the factory method with a decorator.

    See mtt_dummy for examples
    """

    prov_config = config.load(config_label)
    plugin_id = prov_config.get(MTT_PROVISIONER_CONFIG_KEY_PLUGINID)

    return make_provisioner(plugin_id, config, instance_id)

MTT_WORKLOAD_CONFIG_LABEL = 'workloads'
""" new_workloads_from_config will load this config to decide how to build the worklaod plugin """
MTT_WORKLOAD_CONFIG_KEY_WORKLOADS = 'workloads'
""" new_workloads_from_config will get() this config to decide how to build each worklaod plugin """
MTT_WORKLOAD_CONFIG_KEY_PLUGINID = 'plugin_id'
""" new_workloads_from_config will use this Dict key from the worklaod config to decide what plugin to create """
MTT_WORKLOAD_CONFIG_KEY_ARGS = 'arguments'
""" new_workloads_from_config will use this Dict key from the worklaod config to decide what arguments to pass to the plugin """
def new_workloads_from_config(config: Config, label:str=MTT_WORKLOAD_CONFIG_LABEL, key:str=MTT_WORKLOAD_CONFIG_KEY_WORKLOADS) -> Dict[str,WorkloadBase]:
    """ Retrieve a keyed Dict of workload plugins from config

    the config object is used to retrieve workload settings.  A Dict of workload
    plugin conf is loaded, and each config is turned into a plugin.

    Parameters:

    config (Config) : Used to load and get the workload configuration

    Returns:

    Dict[str, WorkloadBase] of workload plugins

    """

    workload_config = config.load(label)
    workload_list = workload_config.get(key)

    #assert isinstance(workload_list, Dict[str, Dict]), "workloads was expected to be a Dict of plugin configuration"

    workloads = {}
    for instance_id, workload_config in workload_list.items():
        plugin_id = workload_config[MTT_WORKLOAD_CONFIG_KEY_PLUGINID]
        workload = make_workload(plugin_id, config, instance_id)

        if MTT_WORKLOAD_CONFIG_KEY_ARGS in workload_config:
            workload.arguments(**workload_config[MTT_WORKLOAD_CONFIG_KEY_ARGS])

        workloads[instance_id] = workload

    return workloads

MTT_CLIENT_CONFIG_LABEL = 'clients'
""" pclients_from_config will load this config to decide how to build the provisioner plugin """
MTT_CLIENT_CONFIG_KEY_CLIENTS = 'clients'
""" clients will get() this config to decide how to build each provisioner plugin """
MTT_CLIENT_CONFIG_KEY_PLUGINID = 'plugin_id'
""" clients_from_config will use this Dict key from the client config to decide what plugin to create """
MTT_CLIENT_CONFIG_KEY_ARGS = 'arguments'
""" new_clients_from_config will use this Dict key from the client config to decide what arguments to pass to the plugin """
def new_clients_from_config(config: Config, label:str=MTT_CLIENT_CONFIG_LABEL, key:str=MTT_CLIENT_CONFIG_KEY_CLIENTS):
    """ Create clients from some config

    This method will interpret some config values as being usable to build a Dict
    of clients from.
    """
    client_config = config.load(label)
    client_list = client_config.get(key)

    if not isinstance(client_list, dict):
        raise ValueError('Did not receive a good dict of client config to make clients from: %s', client_list)
    #assert isinstance(client_list, Dict[str, Dict]), "clients was expected to be a Dict of plugin configuration"

    clients = {}
    for instance_id, client_config in client_list.items():
        plugin_id = client_config[MTT_CLIENT_CONFIG_KEY_PLUGINID]
        client = make_client(plugin_id, config, instance_id)

        if MTT_CLIENT_CONFIG_KEY_ARGS in client_config:
            client.arguments(**clients_config[MTT_CLIENT_CONFIG_KEY_ARGS])

        clients[instance_id] = client

    return clients
