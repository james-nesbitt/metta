"""

Metta client plugin for kubernetes.

This client makes a strong effort to behave as an extension of the community
kubernetes python library, combining this with the metta config system, and
allowing creation by any provisioning source.


"""
import logging
import re
import time
from typing import Dict, Any, List

import kubernetes
from kubernetes.client import models
from kubernetes.client import api

from mirantis.testing.metta.environment import Environment
from mirantis.testing.metta_health.healthcheck import Health, HealthStatus

logger = logging.getLogger("metta.contrib.kubernetes.client.kubeapi")

METTA_PLUGIN_ID_KUBERNETES_CLIENT = "metta_kubernetes_kubeapi_client"
""" client plugin_id for the metta kubernetes client plugin """


KUBEAPI_CLIENT_INTERPRET_Z_REGEX = re.compile(
    r"^\[(?P<symbol>[+-])\](?P<name>\S+)\s{1}(?P<ok>\w+)$"
)


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

    def __init__(self, environment: Environment, instance_id: str, kube_config_file: str = ""):
        """Run the super constructor but also set class properties.

        This implements the args part of the client interface.

        Here we expect to receive a path to a KUBECONFIG file with a context set
        and we create a Kubernetes client for replace_existing=Trueuse.  After
        that this can provide Core api clients as per the kubernetes SDK

        Parameters:
        -----------
        config_file (str): String path to the kubernetes config file to use

        """
        self._environment: Environment = environment
        """ Environemnt in which this plugin exists """
        self._instance_id: str = instance_id
        """ Unique id for this plugin instance """

        logger.debug("Creating Kuberentes client from config file")
        self._api_client = kubernetes.config.new_client_from_config(config_file=kube_config_file)
        """ Kubernetes api client """

        self.config_file = kube_config_file
        """ Kube config file, in case you need to steal it. """

    def info(self, deep: bool = False) -> Dict[str, Any]:
        """Return dict data about this plugin for introspection."""
        info: Dict[str, Any] = {"kubernetes": {"config_file": self.config_file}}

        if deep:
            try:
                info["nodes"] = list(node.to_dict() for node in self.nodes())
            # pylint: disable=broad-except
            except Exception:
                # Still continue to run
                pass

        return info

    def get_api(self, name: str):
        """Get an kubernetes API."""
        if hasattr(kubernetes.client, name):
            return getattr(kubernetes.client, name)(self._api_client)

        raise KeyError(f"Unknown API requested: {api}")

    def utils_create_from_yaml(self, yaml_file: str, **kwargs):
        """Run a kube apply from a yaml file."""
        return kubernetes.utils.create_from_yaml(
            k8s_client=self._api_client, yaml_file=yaml_file, **kwargs
        )

    def utils_create_from_dict(self, data: Dict, **kwargs):
        """Run a kube apply from dict of K8S yaml."""
        return kubernetes.utils.create_from_dict(k8s_client=self._api_client, data=data, **kwargs)

    def nodes(self) -> List[models.v1_node.V1Node]:
        """Return V1Node list.

        Returns:
        --------
        List of kubernetes cluster nodes as V1Node objects.

        You can get node status from node.status.

        """
        node_items = self.get_api("CoreV1Api").list_node().items

        return node_items

    def kubelet_ready_wait(self, timeout: int = 30, period: int = 1):
        """Wait until all nodes' kubelets are ready.

        Some operations need all k8s nodes to be ready or they will fail.
        In such cases the readyz approach does not suffice, as it only
        guarantees that enough nodes are online to allow api calls to
        work.

        """
        err = None
        while timeout > 0:
            try:
                for node in self.nodes():
                    kubelet_condition = node_status_condition(node, "KubeletReady")

                    if not kubelet_condition.status == "True":
                        raise RuntimeError(f"Node kubelet is not ready: {node.metadata.name}")
                return True

            except RuntimeError as this_err:
                logger.debug("node kubelet not ready: %s", this_err)
                err = this_err
                time.sleep(period)
                timeout = timeout - period
                continue

        raise RuntimeError("Timed out waiting for kubernetes to become ready") from err

    def readyz_wait(self, timeout: int = 30, period: int = 1):
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

        raise RuntimeError("Timed out waiting for kubernetes to become ready") from err

    def readyz(self):
        """Check the general readyz endpoint.

        Returns:
        --------
        Dict of service:status_dict with values symbol (+) and string ok value

        Raises:
        -------
        Will raise an exception is kubernetes isn't avaialble

        """
        return self._interpret_z_response("/readyz", params={"verbose": "true"})

    def livez(self):
        """Check the general livez endpoint.

        Returns:
        --------
        Dict of service:status_dict with values symbol (+) and string ok value

        Raises:
        -------
        Will raise an exception is kubernetes isn't available

        """
        return self._interpret_z_response("/livez", params={"verbose": "true"})

    def _interpret_z_response(
        self, endpoint: str, method: str = "GET", params: Dict[str, str] = None
    ) -> Dict[str, Dict[str, str]]:
        """Interpret that readyz/livez response format into a dict.

        because both livez and readyz return similar a machine un-friendly response, we use this
        method to retrieve and interpret the result.

        """
        # this will produce an exception if K8s is not ready
        response = self._api_client.call_api(
            method=method,
            resource_path=endpoint,
            query_params=params if params is not None else {},
            _preload_content=False,
        )[0]

        interpreted = {}
        for line in response.read(cache_content=False).decode("utf-8").split("\n"):
            match = KUBEAPI_CLIENT_INTERPRET_Z_REGEX.fullmatch(line)
            if match:
                interpreted[match.group("name")] = {
                    "symbol": match.group("symbol"),
                    "ok": match.group("ok"),
                }

        return interpreted

    # this allows consumers to get a watch without importing kubernetes
    # pylint: disable=no-self-use
    def watch(self):
        """Get a kubernetes watch instance."""
        return kubernetes.watch.Watch()

    # healthcheck interfaces

    def health(self) -> Health:
        """Determine the health of the K8s instance."""
        k8s_health = Health(source=self._instance_id, status=HealthStatus.UNKNOWN)

        for test_health_function in [
            self._health_k8s_readyz,
            self._health_k8s_livez,
            self._health_k8s_node_health,
            self._health_k8s_alldeployment_health,
            self._health_k8s_alldaemonset_health,
            self._health_k8s_allstatefulset_health,
            self._health_k8s_allpod_health,
        ]:
            try:
                test_health = test_health_function()
            # pylint: disable=broad-except
            except Exception as err:
                test_health = Health(source=self._instance_id)
                test_health.critical(f"{test_health_function} exception: {err}")
            finally:
                k8s_health.merge(test_health)
        return k8s_health

    def _health_k8s_readyz(self) -> Health:
        """Check if kubernetes thinks the pod is healthy."""
        health = Health(source=self._instance_id)

        try:
            if self.readyz():
                health.healthy("KubeAPI: readyz reports ready")
            else:
                health.warning("KubeAPI: readyz reports NOT ready.")
        # pylint: disable=broad-except
        except Exception as err:
            health.error(f"Could not retrieve readyz: {err}")

        return health

    def _health_k8s_livez(self) -> Health:
        """Check if kubernetes thinks the pod is healthy."""
        health = Health(source=self._instance_id)

        try:
            if self.livez():
                health.healthy("KubeAPI: livez reports live")
            else:
                health.warning("KubeAPI: livez reports NOT live.")
        # pylint: disable=broad-except
        except Exception as err:
            health.error(f"Could not retrieve livez: {err}")

        return health

    def _health_k8s_node_health(self) -> Health:
        """Check if kubernetes thinks the nodes are healthy."""
        health = Health(source=self._instance_id)

        try:
            for node in self.nodes():
                name = node.metadata.name
                no_issues = True

                condition = next(
                    (
                        condition
                        for condition in node.status.conditions
                        if condition.type == "Ready"
                    ),
                    None,
                )
                if condition is not None and condition.status != "True":
                    health.warning(f"KubeAPI: {name}: {condition.message}")
                    no_issues = False

                condition = next(
                    (
                        condition
                        for condition in node.status.conditions
                        if condition.type == "NetworkUnavailable"
                    ),
                    None,
                )
                if condition is not None and condition.status == "True":
                    health.warning(f"KubeAPI: {name}: {condition.message}")
                    no_issues = False

                condition = next(
                    (
                        condition
                        for condition in node.status.conditions
                        if condition.type == "MemoryPressure"
                    ),
                    None,
                )
                if condition is not None and condition.status == "True":
                    health.warning(f"KubeAPI: {name}: {condition.message}")
                    no_issues = False

                condition = next(
                    (
                        condition
                        for condition in node.status.conditions
                        if condition.type == "DiskPressure"
                    ),
                    None,
                )
                if condition is not None and condition.status == "True":
                    health.warning(f"KubeAPI: {name}: {condition.message}")
                    no_issues = False

                condition = next(
                    (
                        condition
                        for condition in node.status.conditions
                        if condition.type == "PIDPressure"
                    ),
                    None,
                )
                if condition is not None and condition.status == "True":
                    health.warning(f"KubeAPI: {name}: {condition.message}")
                    no_issues = False

                if no_issues:
                    health.healthy(f"KubeAPI: Node {name} reports healthy.")
                else:
                    health.error(f"KubeAPI: Node {name} reporting issues.")

        # pylint: disable=broad-except
        except Exception as err:
            health.error(f"KubeAPI:Exception occured when check kubelet health: {err}")

        return health

    # pylint: disable=too-many-branches
    def _health_k8s_alldeployment_health(self) -> Health:
        """Check if kubernetes thinks all the deployments are healthy."""
        health = Health(source=self._instance_id)

        apps_v1_api: api.apps_v1_api.AppsV1Api = self.get_api("AppsV1Api")

        unhealthy_dep_count = 0
        # pylint: disable=no-member
        for deployment in apps_v1_api.list_deployment_for_all_namespaces().items:
            namespace = deployment.metadata.namespace
            name = deployment.metadata.name

            no_issues = True

            if not deployment.status.conditions:
                health.unknown(
                    f"KubeAPI:Deployment: [{namespace}/{name}] "
                    "Deployment does not have any conditions (yet?)"
                )
                continue

            available_condition = next(
                (
                    condition
                    for condition in deployment.status.conditions
                    if condition.type == "Available"
                ),
                None,
            )
            progressing_condition = next(
                (
                    condition
                    for condition in deployment.status.conditions
                    if condition.type == "Progressing"
                ),
                None,
            )
            if available_condition and available_condition.status == "True":
                pass
            elif progressing_condition and progressing_condition.status == "True":
                health.warning(
                    f"KubeAPI:Deployment: [{namespace}/{name}] "
                    "Deployment is progressing "
                    f"-> {progressing_condition.message}"
                )
                no_issues = False
            else:
                messages = "\n".join(
                    list(
                        condition.message
                        for condition in [progressing_condition, available_condition]
                        if condition is not None
                    )
                )
                health.warning(
                    f"KubeAPI:Deployment: [{namespace}/{name}] "
                    "Deployment is neither progressing nor available "
                    f"-> {messages}"
                )
                no_issues = False

            for condition in deployment.status.conditions:
                if condition.type in ["Available", "Progressing"]:
                    pass

                elif condition.status != "True":
                    health.warning(
                        f"KubeAPI:Deployment: [{namespace}/{name}] {condition.type} "
                        f"-> {condition.message}"
                    )
                    no_issues = False

            if no_issues:
                health.healthy(f"KubeAPI:Deployment: [{namespace}/{name}] is healthy")
            else:
                health.warning(f"KubeAPI:Deployment: [{namespace}/{name}] is not healthy")
                unhealthy_dep_count += 1

        if unhealthy_dep_count == 0:
            health.healthy("KubeAPI: all deployments report healthy")
        elif unhealthy_dep_count < 3:
            health.warning("KubeAPI: some deployments report condition failures")
        else:
            health.error("KubeAPI: Kubernetes Reports cluster is unhealthy (deployment health)")

        return health

    def _health_k8s_alldaemonset_health(self) -> Health:
        """Check if kubernetes thinks all the daemonsets are healthy."""
        health = Health(source=self._instance_id)

        apps_v1_api: api.apps_v1_api.AppsV1Api = self.get_api("AppsV1Api")

        unhealthy_dae_count = 0
        # pylint: disable=no-member
        for daemonset in apps_v1_api.list_daemon_set_for_all_namespaces().items:
            namespace = daemonset.metadata.namespace
            name = daemonset.metadata.name
            status = daemonset.status

            if status.collision_count is not None and status.collision_count > 0:
                health.warning(
                    f"Daemonset: [{namespace}/{name}] collision_count "
                    "-> Reports some collisions: "
                    f"{status.collision_count}"
                )
                unhealthy_dae_count += 1
            if status.number_unavailable is not None and status.number_unavailable > 0:
                health.warning(
                    f"Daemonset: [{namespace}/{name}] number_unavailable "
                    "-> Reports some unavailable pods: "
                    f"{status.number_unavailable}"
                )
                unhealthy_dae_count += 1
            if status.desired_number_scheduled < status.current_number_scheduled:
                health.warning(
                    f"Daemonset: [{namespace}/{name}] desired_number_scheduled "
                    "-> Does not have the desired number scheduled: "
                    f"{status.desired_number_scheduled} < "
                    f"{status.current_number_scheduled}"
                )
                unhealthy_dae_count += 1

            if status.conditions:
                for condition in status.conditions:
                    if condition.status == "True":
                        health.healthy(
                            f"Daemonset: [{namespace}/{name}] {condition.type} "
                            f"-> {condition.message}"
                        )
                    else:
                        health.warning(
                            f"Daemonset: [{namespace}/{name}] {condition.type} "
                            f"-> {condition.message}"
                        )
                        unhealthy_dae_count += 1

        if unhealthy_dae_count == 0:
            health.healthy("KubeAPI: all daemonsets report as healthy")
        elif unhealthy_dae_count < 3:
            health.warning("KubeAPI: some daemonsets report condition failures")
        else:
            health.error("KubeAPI: Kubernetes Reports cluster is unhealthy (daemonset health)")

        return health

    def _health_k8s_allstatefulset_health(self) -> Health:
        """Check if kubernetes thinks all the statefulsets are healthy."""
        health = Health(source=self._instance_id)

        apps_v1_api: api.apps_v1_api.AppsV1Api = self.get_api("AppsV1Api")

        unhealthy_count = 0
        # pylint: disable=no-member
        for statefulset in apps_v1_api.list_stateful_set_for_all_namespaces().items:
            namespace = statefulset.metadata.namespace
            name = statefulset.metadata.name
            status = statefulset.status

            # {'collision_count': 0,
            #  'conditions': None,
            #  'current_replicas': 1,
            #  'current_revision': 'loki-workload-67877b465c',
            #  'observed_generation': 1,
            #  'ready_replicas': 1,
            #  'replicas': 1,
            #  'update_revision': 'loki-workload-67877b465c',
            #  'updated_replicas': 1}

            if status.collision_count is not None and status.collision_count > 0:
                health.warning(
                    f"KubeAPI:Statefulset: [{namespace}/{name}] "
                    "-> Reports some collisions: "
                    f"{status.collision_count}"
                )
                unhealthy_count += 1

            if status.conditions:
                for condition in status.conditions:
                    if condition.status == "True":
                        health.healthy(
                            f"KubeAPI:Statefulset: [{namespace}/{name}] {condition.type} "
                            f"-> {condition.message}"
                        )
                    else:
                        health.warning(
                            f"KubeAPI:Statefulset: [{namespace}/{name}] {condition.type} "
                            f"-> {condition.message}"
                        )
                        unhealthy_count += 1

        if unhealthy_count == 0:
            health.healthy("KubeAPI: all statefulsets report as healthy")
        elif unhealthy_count < 3:
            health.warning("KubeAPI: some statefulsets report condition failures")
        else:
            health.error("KubeAPI: Kubernetes Reports cluster is unhealthy (statefulset health)")

        return health

    def _health_k8s_allpod_health(self) -> Health:
        """Check if kubernetes thinks all the pods are healthy."""
        health = Health(source=self._instance_id)

        core_v1_api = self.get_api("CoreV1Api")

        unhealthy_pod_count = 0
        for pod in core_v1_api.list_pod_for_all_namespaces().items:
            if pod.status.phase == "Failed":
                health.error(f"KubeAPI: pod failed: {pod.metadata.name}")
                unhealthy_pod_count += 1
        if unhealthy_pod_count == 0:
            health.healthy("KubeAPI: all pods report as healthy")
        elif unhealthy_pod_count < 2:
            health.warning("KubeAPI: some pods report as failed")
        else:
            health.error("KubeAPI: Kubernetes Reports cluster is unhealthy (pod health)")

        return health


def node_status_condition(
    node: models.v1_node.V1Node, cond_reason: str, cond_type: str = "Ready"
) -> models.v1_node_condition.V1NodeCondition:
    """Retrieve a status condition of matching reason from a node."""
    status: models.v1_node_status.V1NodeStatus = node.status

    for condition in status.conditions:
        if condition.reason == cond_reason and condition.type == cond_type:
            return condition
    raise RuntimeError(f"No matching condition found for {cond_reason}/{cond_type}")
