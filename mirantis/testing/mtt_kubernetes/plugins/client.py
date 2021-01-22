
import kubernetes
import logging

from mirantis.testing.mtt.client import ClientBase

logger = logging.getLogger("mirantis.testing.mtt_kubernetes.client")

class KubernetesClientPlugin(ClientBase):
    """ MTT Client plugin for Kubernetes

    Construction:
    -------------

    As an MTT Plugin, the class constructor is used to initialize the instance
    as a plugin.  This means that we lose the constructor, but we gain access
    to an mtt.config.Config object.

    We use .args() to configure the instance and create the client, as per the
    client plugin standard.

    To use:
    -------

    2. Ask mtt.client.make_client for an instance of the plugin
        a. it is more expected that a provisioner will provide the client directly
        b. you can ask for the plugin directly from mtt.plugin.get_plugin()
        c. you can use mtt.new_clients_from_config() if you have some configuration
           with the needed args, and it will build clients for you
    3. Configure using .args() adding a kubeconfig file (with activated context)
       if that wasn't done for you when you received the client
    4. Ask the client for a kubernetes API version client
       (such as get_CoreV1Api_client => CoreV1Api)
    5. Use the kubernetes API client as normal

    ```
    import mirantis.testing.mtt as mtt
    import mirantis.testing.mtt.client as mtt_client
    import mirantis.testing.mtt_kubernetes as mtt_kubernetes

    config = mtt.new_config()
    client = mtt_client.make_client(mtt_kubernetes.MTT_PLUGIN_ID_KUBERNETES_CLIENT, config, 'my-k8-instance')

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

    def args(self, config_file: str):
        """ set Kubernetes client args

        This implements the args part of the client interface.

        Here we expect to receive a path to a KUBECONFIG file with a context set
        and we create a Kubernetes client for use.  After that this can provide
        Core api clients as per the kubernetes SDK

        Parameters:
        -----------

        config_file (str): String path to the kubernetes config file to use

        """
        logger.debug("Creating Kuberentes client from config file")
        self.api_client = kubernetes.config.new_client_from_config(config_file=config_file)

    def get_CoreV1Api_client(self):
        """ Get a CoreV1Api client """
        logger.debug("Retrieving kubernetes CoreV1Api client from api_client")
        return kubernetes.client.CoreV1Api(self.api_client)
