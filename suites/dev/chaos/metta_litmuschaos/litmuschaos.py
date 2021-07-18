"""

Litmus Chaos client/tooling

This module contains the supporting tooling for implementing Litmus Chaos in
a kubernetes cluster.  It supports any Metta plugin or functionality that wants
Litmus Integration.

"""
import logging
import time
from typing import List

import requests
import yaml

logger = logging.getLogger("litmuschaos.client")

LITMUSCHAOS_YAML_RBAC_PERMISSIVE = """---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: litmus
  namespace: default
  labels:
    name: litmuschaos
---
apiVersion: rbac.authorization.k8s.io/v1beta1
kind: ClusterRole
metadata:
  name: litmus
rules:
  -
    apiGroups:
      - ""
      - apps
      - autoscaling
      - batch
      - extensions
      - policy
      - rbac.authorization.k8s.io
    resources:
      - componentstatuses
      - configmaps
      - daemonsets
      - deployments
      - events
      - endpoints
      - horizontalpodautoscalers
      - ingress
      - jobs
      - limitranges
      - namespaces
      - nodes
      - pods
      - persistentvolumes
      - persistentvolumeclaims
      - resourcequotas
      - replicasets
      - replicationcontrollers
      - serviceaccounts
      - services
    verbs: ["*"]
  - nonResourceURLs: ["*"]
    verbs: ["*"]
---
apiVersion: rbac.authorization.k8s.io/v1beta1
kind: ClusterRoleBinding
metadata:
  name: litmuschaos-api-accessdeployment
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: litmus
subjects:
- kind: ServiceAccount
  name: litmus
  namespace: default"""
""" A very broad access RBAC service account.  Note that in the destroy() method we
ended up expecting a certain set of resources to be deleted, but that is a WIP """


LITMUSCHAOS_OPERATOR_DEFAULT_VERSION = "v1.13.3"
""" LC version used to determine urls/paths for includes """
LITMUSCHAOS_CONFIG_DEFAULT_EXPERIMENTS = ["charts/generic/experiments.yaml"]
""" Default value for litmus chaos experiments to run. """

LITMUSCHAOS_OPERATOR_URL_PATTERN = (
    "https://litmuschaos.github.io/litmus/litmus-operator-v{version}.yaml"
)
""" URL pattern to the LC operator kubernetes yaml - needs version """

LITMUSCHAOS_OPERATOR_EXPERIMENT_PATTERN = (
    "https://hub.litmuschaos.io/api/chaos/{version}?file={experiment}"
)
""" URL pattern to the LC experiment yaml - needs version and experiment yaml chart path """


class LitmusChaos:
    """Manage Litmus Chaos in a Kubernetes cluster."""

    def __init__(
        self,
        kube_client: str,
        namespace: str,
        version: str = LITMUSCHAOS_OPERATOR_DEFAULT_VERSION,
        experiments: List[str] = None,
    ):
        """
        Parameters:
        -----------

        kube_client (str) : metta_kubernets kubeapi client object, which will
            be used to interact with the kubernetes cluster.

        namespace (str) : kubernetes namespace to use for chaos engineering

        version (str) : litmus chaos version to use

        experiments (List[str]) : litmus chaos experiments to run
        """
        self.kube_client = kube_client
        self.namespace = namespace
        self.version = version
        self.experiments = (
            experiments if experiments is not None else LITMUSCHAOS_CONFIG_DEFAULT_EXPERIMENTS
        )

    def info(self):
        """Return an object/dict of inforamtion about the instance for debugging."""
        info = {"kubeconfig": self.kube_client.config_file, "namespace": self.namespace}

        return info

    def prepare(self):
        """Prepare to run litmus chaos by installing all of the pre-requisites

        @see: hhttps://docs.litmuschaos.io/docs/getstarted/#uninstallation

        1. install the LitmusChaos operator:RbacAuthorizationV1Api
            '''kubectl apply -f https://litmuschaos.github.io/litmus/litmus-operator-v1.13.3.yaml'''

           verify instalation
            '''kubectl get pods -n litmus'''
            '''kubectl get crds | grep chaos'''
            '''kubectl api-resources | grep chaos'''

        2. install experiments:
           '''kubectl apply -f \
              https://hub.litmuschaos.io/api/chaos/1.13.3?file=charts/generic/experiments.yaml \
              -n nginx'''

        3. setup service account
            figure out your rbac and apply it.

            @NOTE we are going to start with a really permissive CRB for initial testing
            @TODO dial back this RBAC to something more appropriate

        """
        # 1. get and install the operator
        with requests.get(
            LITMUSCHAOS_OPERATOR_URL_PATTERN.format(version=self.version),
            allow_redirects=True,
        ) as res:

            resources_yaml = yaml.safe_load_all(res.text)

            for resource in resources_yaml:
                self.kube_client.utils_create_from_dict(data=resource, namespace=self.namespace)

        time.sleep(10)

        # 2. install experiments
        for experiment in self.experiments:
            with requests.get(
                LITMUSCHAOS_OPERATOR_EXPERIMENT_PATTERN.format(
                    version=self.version, experiment=experiment
                ),
                allow_redirects=True,
            ) as res:

                resources_yaml = yaml.safe_load_all(res.text)
                for resource in resources_yaml:
                    self.kube_client.utils_create_from_dict(data=resource, namespace=self.namespace)

        # 3. RBAC
        self.kube_client.utils_create_from_yaml(
            yaml.safe_load(LITMUSCHAOS_YAML_RBAC_PERMISSIVE), namespace=self.namespace
        )

    def apply(self):
        """Run the Litmus Chaos experiments."""

    def destroy(self):
        """Remove all litmus chaos components from the cluster.

        @NOTE this currently does not strictly follow the documentation.
          Currently we only:

          1. delete the litmus namespace
          2. remove the custom operator CRD

        @see: https://docs.litmuschaos.io/docs/getstarted/#uninstallation

        1. delete any chaos-engines running
            '''kubectl delete chaosengine --all -n <namespace>'''

        2. remove the litmus chaos created namespace resources
            '''kubectl delete \
                  -f https://litmuschaos.github.io/litmus/litmus-operator-v1.13.3.yaml'''

        """
        core = self.kube_client.get_api("CoreV1Api")
        rbac = self.kube_client.get_api("RbacAuthorizationV1Api")
        extensions = self.kube_client.get_api("ApiextensionsV1Api")

        # Remove the RBAC
        core.delete_namespaced_service_account("litmus", "litmus")
        rbac.delete_cluster_role("litmus")
        rbac.delete_cluster_role_binding("litmus")

        # Remove the Litmus namespace
        core.delete_namespace("litmus", grace_period_seconds=30, propagation_policy="Foreground")

        # Remove the litmus CRDs
        extensions.delete_custom_resource_definition(
            "chaosengines.litmuschaos.io",
            grace_period_seconds=30,
            propagation_policy="Foreground",
        )
        extensions.delete_custom_resource_definition(
            "chaosexperiments.litmuschaos.io",
            grace_period_seconds=30,
            propagation_policy="Foreground",
        )
        extensions.delete_custom_resource_definition(
            "chaosresults.litmuschaos.io",
            grace_period_seconds=30,
            propagation_policy="Foreground",
        )
