"""

Metta client plugin for kubernetes.

This client makes a strong effort to behave as an extension of the community
kubernetes python library, combining this with the metta config system, and
allowing creation by any provisioning source.


"""
import logging
import re
import time
from typing import Dict, Any

import kubernetes

logger = logging.getLogger('metta.contrib.kubernetes.client.kubeapi')

METTA_PLUGIN_ID_KUBERNETES_CLIENT = 'metta_kubernetes'
""" client plugin_id for the metta kubernetes client plugin """

KUBEAPI_CLIENT_INTERPRET_Z_REGEX = re.compile(
    r'^\[(?P<symbol>[+-])\](?P<name>\S+)\s{1}(?P<ok>\w+)$')


class KubernetesApiClientPlugin:
    """Metta Client plugin for Kubernetes.

    Construction:
    -------------
    As an metta Plugin, the class constructor is used to initialize the
    instance as a plugin.  This means that we lose the constructor, but we gain
    access to an metta.config.Config object.

    We use .args() to configure the instance and create the client, as per the
    client plugin standard.

    To use:
    -------

    2. Ask metta.client.make_client for an instance of the plugin
        a. it is more expected that a provisioner will provide the client
           directly
        b. you can ask for the plugin directly from metta.plugin.get_plugin()
        c. you can use metta.new_clients_from_config() if you have some
           configuration with the needed args, and it will build clients for
           you
    3. Configure using .args() adding a kubeconfig file with activated context
       if that wasn't done for you when you received the client
    4. Ask the client for a kubernetes API version client
       (such as get_api('CoreV1Api') => CoreV1Api)
    5. Use the kubernetes API client as normal

    ```
    import mirantis.testing.metta as metta
    import mirantis.testing.metta.client as metta_client
    import mirantis.testing.metta_kubernetes as metta_kubernetes

    config = metta.new_config()
    client = metta_client.make_client(
                metta_kubernetes.METTA_PLUGIN_ID_KUBERNETES_CLIENT,
                config, 'my-k8-instance')

    client.args('path/to/k8file')

    core_v1 = client.get_api('CoreV1Api')
    ns = core_v1.read_namespace(name="kube-system")
    print(f"NS: {ns}")
    ```

    Why use this:
    -------------
    It is cumbersome to use this if you already have access to the kubeconfig,
    but it fits into the plugin system, and therefore auto-loading and
    auto-configuring is possible with this implementation.
    Effectively, it is not easier to use this plu-gin over the native K8 client
    unless you consider that a provisioner can provide you this plugin already
    configured with its own information.

    This plugin is particularly usefull as it can be used for the helm and
    deployment workload plugins directly, which know how to use it to apply
    workloads to a kubernetes cluster.

    """

    def __init__(self, environment, instance_id, kube_config_file: str = ''):
        """Run the super constructor but also set class properties.

        This implements the args part of the client interface.

        Here we expect to receive a path to a KUBECONFIG file with a context set
        and we create a Kubernetes client for use.  After that this can provide
        Core api clients as per the kubernetes SDK

        Parameters:
        -----------
        config_file (str): String path to the kubernetes config file to use

        """
        self.environment = environment
        """ Environemnt in which this plugin exists """
        self.instance_id = instance_id
        """ Unique id for this plugin instance """

        logger.debug("Creating Kuberentes client from config file")
        self.api_client = kubernetes.config.new_client_from_config(
            config_file=kube_config_file)
        """ Kubernetes api client """

        self.config_file = kube_config_file
        """ Kube config file, in case you need to steal it. """

    def info(self) -> Dict[str, Any]:
        """Return dict data about this plugin for introspection."""
        return {
            'kubernetes': {
                'config_file': self.config_file
            }
        }

    def get_api(self, api: str):
        """Get an kubernetes API."""
        if hasattr(kubernetes.client, api):
            return getattr(kubernetes.client, api)(self.api_client)

        raise KeyError(f"Unknown API requested: {api}")

    def utils_create_from_yaml(self, yaml_file: str, **kwargs):
        """Run a kube apply from a yaml file."""
        return kubernetes.utils.create_from_yaml(
            k8s_client=self.api_client, yaml_file=yaml_file, **kwargs)

    def utils_create_from_dict(self, data: Dict, **kwargs):
        """Run a kube apply from dict of K8S yaml."""
        return kubernetes.utils.create_from_dict(
            k8s_client=self.api_client, data=data, **kwargs)

    def ready_wait(self, timeout: int = 30, period: int = 1):
        """Wait until kubernetes is ready before returning."""
        err = None
        while timeout > 0:
            try:
                ready = self.readyz()
                return ready
            except kubernetes.client.rest.ApiException as this_err:
                err = this_err
                time.sleep(period)
                timeout = timeout - period
                continue

        raise RuntimeError('Timed out waiting for kubernetes to become ready') from err

    def readyz(self):
        """Check the general readyz endpoint.

        Returns:
        --------
        Dict of service:status_dict with values symbol (+) and string ok value

        Raises:
        -------
        Will raise an exception is kubernetes isn't avaialble

        """
        return self._interpret_z_response('/readyz')

    def livez(self):
        """Check the general livez endpoint.

        Returns:
        --------
        Dict of service:status_dict with values symbol (+) and string ok value

        Raises:
        -------
        Will raise an exception is kubernetes isn't avaialble

        """
        return self._interpret_z_response('/livez')

    def _interpret_z_response(self, endpoint: str, method: str = 'GET',
                              params: Dict[str, str] = None) -> Dict[str, Dict[str, str]]:
        """Interpret that readyz/livez response format into a dict.

        because both livez and readyz return similar a machine un-friendly response, we use this
        method to retrieve and interpret the result.

        """
        # this will produce an exception if K8s is not ready
        response = self.api_client.call_api(
            method=method,
            resource_path=endpoint,
            query_params=params if params is not None else {},
            _preload_content=False)[0]

        interpreted = {}
        for line in response.read().decode("utf-8") .split('\n'):
            match = KUBEAPI_CLIENT_INTERPRET_Z_REGEX.fullmatch(line)
            if match:
                interpreted[match.group('name')] = {
                    'symbol': match.group('symbol'),
                    'ok': match.group('ok')
                }

        return interpreted

    # this allows consumers to get a watch without importing kubernetes
    # pylint: disable=no-self-use
    def watch(self):
        """Get a kubernetes watch instance."""
        return kubernetes.watch.Watch()
