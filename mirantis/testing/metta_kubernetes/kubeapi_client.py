
import kubernetes
import logging

from mirantis.testing.metta.client import ClientBase

logger = logging.getLogger('metta.contrib.kubernetes.client.kubeapi')


class KubernetesApiClientPlugin(ClientBase):
    """ metta Client plugin for Kubernetes

    Construction:
    -------------

    As an metta Plugin, the class constructor is used to initialize the instance
    as a plugin.  This means that we lose the constructor, but we gain access
    to an metta.config.Config object.

    We use .args() to configure the instance and create the client, as per the
    client plugin standard.

    To use:
    -------

    2. Ask metta.client.make_client for an instance of the plugin
        a. it is more expected that a provisioner will provide the client directly
        b. you can ask for the plugin directly from metta.plugin.get_plugin()
        c. you can use metta.new_clients_from_config() if you have some configuration
           with the needed args, and it will build clients for you
    3. Configure using .args() adding a kubeconfig file (with activated context)
       if that wasn't done for you when you received the client
    4. Ask the client for a kubernetes API version client
       (such as get_CoreV1Api_client => CoreV1Api)
    5. Use the kubernetes API client as normal

    ```
    import mirantis.testing.metta as metta
    import mirantis.testing.metta.client as metta_client
    import mirantis.testing.metta_kubernetes as metta_kubernetes

    config = metta.new_config()
    client = metta_client.make_client(metta_kubernetes.METTA_PLUGIN_ID_KUBERNETES_CLIENT, config, 'my-k8-instance')

    client.args('path/to/k8file')

    coreV1 = client.get_CoreV1Api_client()
    ns = coreV1.read_namespace(name="kube-system")
    print("NS: {}".format(ns))
    ```

    Why use this:
    -------------

    It is cumbersome to use this if you already have access to the kubeconfig, but
    it fits into the plugin system, and therefore auto-loading and auto-configuring
    is possible with this implementation.
    Effectively, it is not easier to use this plugin over the native K8 client unless
    you consider that a provisioner can provide you this plugin already configured
    with its own information.

    """

    def __init__(self, environment, instance_id, kube_config_file: str = ''):
        """ Run the super constructor but also set class properties

        This implements the args part of the client interface.

        Here we expect to receive a path to a KUBECONFIG file with a context set
        and we create a Kubernetes client for use.  After that this can provide
        Core api clients as per the kubernetes SDK

        Parameters:
        -----------

        config_file (str): String path to the kubernetes config file to use

        """
        super(ClientBase, self).__init__(environment, instance_id)

        logger.debug("Creating Kuberentes client from config file")
        self.api_client = kubernetes.config.new_client_from_config(
            config_file=kube_config_file)

        self.config_file = kube_config_file

    def get_CoreV1Api_client(self):
        """ Get a CoreV1Api client """
        assert self.api_client, "You must run the arguments() method before using this client"

        logger.debug("Retrieving kubernetes CoreV1Api client from api_client")
        return kubernetes.client.CoreV1Api(self.api_client)

    def info(self):
        """ Return dict data about this plugin for introspection """
        return {
            'kubernetes': {
                'config_file': self.config_file
            }
        }
