"""

Provisioner plugin for installing MKE.

Installs MKE with access to a set of hosts with docker installed and
executable capacity (SSH/WinRM.)

"""

METTA_MIRANTIS_PROVISIONER_MKE_PLUGIN_ID = "mirantis_mke_provisioner"
""" Mirantis MKE API Provisioner plugin id """

METTA_MIRANTIS_MKE_CONFIG_LABEL = "mke"
"""Configerus load() label for finding MKE provisioner configuration."""


class MKEProvisionerPlugin:
    """MKE Installer provisioner plugin."""

    # pylint: disable=too-many-arguments"
    def __init__(
        self,
        environment: Environment,
        instance_id: str,
        label: str = TERRAFORM_PROVISIONER_CONFIG_LABEL,
        base: Any = LOADED_KEY_ROOT,
    ):
        """Run the super constructor but also set class properties.

        Interpret provided config and configure the object with all of the
        needed pieces for executing terraform commands

        """
        self._environment = environment
        """ Environemnt in which this plugin exists """
        self._instance_id = instance_id
        """ Unique id for this plugin instance """

        self._config_label = label
        """ configerus load label that should contain all of the config """
        self._config_base = base
        """ configerus get key that should contain all tf config """

        self.fixtures: Fixtures = Fixtures()
        """Children fixtures, typically just the client plugin."""

        try:
            self.make_fixtures()
            # pylint: disable= broad-except
        except Exception as err:
            # there are many reasons this can fail, and we just want to
            # see if we can get fixtures early.
            # No need to ask forgiveness for this one.
            logger.debug("Could not make initial fixtures: %s", err)

    def _install_mke(self):
        """Install UCP.

        ref: https://docs.docker.com/ee/ucp/admin/install/

        :param: mke_obj            (UCP) UCP object reference
        :param: ucp_repo       (str) The hub repo, i.e., 'docker' or 'dockereng'
        :param: ucp_tag        (str) The hub tag, i.e., '3.1.2' or '3.2.0-e910ad4'
        :param: force_workers_to_join (bool) If True, workers will be removed from
                                 the swarm, then rejoin in batches of 10 after UCP
                                 is installed. This is very time consuming for large
                                 (100 node) clusters, but may improve the odds of
                                 a successful install. Default is False
        :return: A command_record.CommandRecord object for the install command sent.
        """
        mke_config = self._environment.config.load(self._config_label)
        """Loaded config that should contain all of our settings as self._config_base."""

        bootstrapper_name = mke_config.get([self._config_base, "bootstrapper"], default="ucp")

        if mke_obj.mgr_node is None:
            mke_obj.mgr_node = mke_obj.cluster.swarm_leader()

        # The docker image.
        mke_obj.bootstrapper_name = toolbox.common.get_ucp_bootstrapper_name(hub_repo, hub_tag)
        log("Installing UCP version {0}".format(mke_obj.bootstrapper_name))
        mke_obj.pull_ucp_images(mke_obj.bootstrapper_name)

        # Tear down the cluster so the install follows the docs (install UCP on a single
        # node, then join managers, then join workers.)
        # get all the managers except for the leader.
        replicants, workers = mke_obj.survey_cluster()
        mke_obj.demote_replicants(replicants)
        if force_workers_to_join:
            mke_obj.cluster.leave_swarm(workers, drain_first=False)

        # Additional install features that we don't currently support:
        #
        # If we have a subscription file (a .lic file) from store, we can SCP the
        # file to the node, and then have UCP use it during the install.
        # If we SCP the file to /config/docker_subscription.lic, then we can:
        # subscription_mount "-v /var/tmp/docker_subscription.lic:/config/docker_subscription.lic"
        subscription_mount = ""
        # The SANs define the DNS entries (or IP addresses) used to sign the certs
        # by UCP, including for an admin bundle. UCP will automatically include the
        # IP address of the host where we did the install, but for AWS the host does
        # not know its public IP address. Since we do know it, we need to use the
        # '--san ' mechanism to tell UCP about it.
        #
        # If there is an ELB in front of us, we would need to include the
        # DNS name (and/or the route53 DNS name) for that here as well.
        sans = "--san {0} --san {1}".format(mke_obj.mgr_node.public_ip, mke_obj.mgr_node.private_ip)
        # If there is an external ELB for deployed apps, we can tell UCP about it.
        # This allows UCP UI to display a nice URL for any apps we deploy.
        # --external-service-lb https://<DNS-name-for-ELB-or-route53>
        service_lb = ""
        # For public swarm on AWS, need to set the '--host-address' value on
        # install. This is the address UCP advertises to new nodes for reconcile.
        # Note that this is typically only needed for Z-node testing.
        # --host-address = mgr_node.public_ip
        host_address_setting = ""
        # to enable debug for the install. Note that if we set this, UCP will
        # run in debug mode unless/until we set UCP logging level to 'INFO'
        # until we do, UCP will emit a ton of debug information in its containers,
        # which can fill up the host's file system.
        # install_debug = '--debug'
        install_debug = ""
        # Testkit installs the engine so it is listening on port TCP 2376.
        # A 'normal' install (i.e., how DCI does it) has the engine listening
        # on a unix-domain (local) socket and swarm listening on port 2376.
        # So for a testkit installed engine, we need to use a different port for
        # swarm. We arbitrarily choose 3376.
        swarm_port = "3376"
        # Determine whether to enable the Ingress istio option or not
        istio = ""
        if self._sys_config.enable_istio:
            istio = "--istio"
        # For Hub repos other than docker, this becomes
        # 'image version dev: '
        mke_obj.image_list_args = image_version_dev(mke_obj.bootstrapper_name)
        # For hosts with SE-linux enabled, we need '--security-opt label=disable'
        security_opt = mke_obj.set_security_option()
        command = (
            "docker container run --rm --name ucp "
            "{subscr} "
            "{sec_opt} "
            "-v /var/run/docker.sock:/var/run/docker.sock "
            "{bootstrapper} "
            "install "
            "{istio} "
            "{sans} "
            "{service_lb} "
            "{host_address_setting} "
            "{install_debug} "
            "--admin-username admin "
            "--admin-password '{admin_password}' "
            "--swarm-port {swarm_port} "
            "{image_list_args}"
        ).format(
            subscr=subscription_mount,
            sec_opt=security_opt,
            bootstrapper=mke_obj.bootstrapper_name,
            istio=istio,
            sans=sans,
            service_lb=service_lb,
            host_address_setting=host_address_setting,
            install_debug=install_debug,
            admin_password=mke_obj.admin_password,
            swarm_port=swarm_port,
            image_list_args=mke_obj.image_list_args,
        )

        # 900 seconds = 15 minutes = the UCP container run timeout
        install_result = mke_obj.mgr_node.send_docker(command, timeout=900)
        if not toolbox.common.wait_for_true(
            mke_obj.verify_version,
            UCP_STABILIZATION_TIMEOUT_SECONDS,
            mke_obj.bootstrapper_name,
            raise_on_fail=False,
        ):
            raise TestException("Unable to verify UCP version is {}".format(hub_tag))
        if not toolbox.common.wait_for_true(
            mke_obj.verify_health,
            UCP_STABILIZATION_TIMEOUT_SECONDS,
            raise_on_fail=False,
        ):
            raise TestException("UCP nodes not healthy following install")
        # now re-promote the replicants
        mke_obj.promote_replicants(replicants)
        if force_workers_to_join:
            # and join the workers ten at a time
            mke_obj.rejoin_workers(workers)

        mke_obj.mgr_node = None
        return install_result

    def _upgrade_mke(self, mke_obj, upgrade_repo, upgrade_tag):
        """
        Upgrade MKE(UCP)
        :param: upgrade_repo   (str) The hub repo, i.e., 'docker' or 'dockereng'
        :param: upgrade_tag    (str) The hub tag, i.e., '3.1.2' or '3.2.0-e910ad4'
        :return: A command_record.CommandRecord object for the upgrade command sent
                 or None if no upgrade has been performed
        """
        new_bootstrapper_name = toolbox.common.get_ucp_bootstrapper_name(upgrade_repo, upgrade_tag)

        if mke_obj.verify_version(new_bootstrapper_name, raise_on_fail=False):
            log("UCP already at version {}. Skipping.".format(new_bootstrapper_name))
            return None

        # make sure we are healthy before doing the upgrade
        log("Performing health check prior to UCP upgrade...")
        mke_obj.verify_health(raise_on_fail=True)

        mke_obj.mgr_node = mke_obj.cluster.swarm_leader()
        # The docker image.
        log(
            "Upgrading UCP from {0} to {1}".format(mke_obj.bootstrapper_name, new_bootstrapper_name)
        )

        mke_obj.pull_ucp_images(new_bootstrapper_name)

        # For public swarm on AWS, need to set the '--host-address' value on
        # upgrade. This is the address UCP advertises to new nodes for reconcile.
        # Note that this is typically only needed for Z-node testing.
        # --host-address = mgr_node.public_ip
        host_address_setting = ""

        # to enable debug for the install. Note that if we set this, UCP will
        # run in debug mode unless/until we set UCP logging level to 'INFO'
        # until we do, UCP will emit a ton of debug information in its containers,
        # which can fill up the host's file system.
        # upgrade_debug = '--debug'
        upgrade_debug = ""

        # For Hub repos other than docker, this becomes
        # 'image version dev: '
        image_list_args = image_version_dev(new_bootstrapper_name)
        # For hosts with SE-linux enabled, we need '--security-opt label=disable'
        security_opt = mke_obj.set_security_option()

        # get UCP ID
        ucp_id = mke_obj.ucp_id

        log("Making backup prior to upgrade.", "Info")
        mke_obj.backup(mke_obj.namespace, mke_obj.version)

        command = (
            "docker container run --rm --name ucp "
            "{sec_opt} "
            "-v /var/run/docker.sock:/var/run/docker.sock "
            "{bootstrapper} "
            "upgrade "
            "{host_address_setting} "
            "{upgrade_debug} "
            "--admin-username admin "
            "--admin-password '{admin_password}' "
            "--id '{ucp_id}' "
            "{image_list_args}"
        ).format(
            sec_opt=security_opt,
            bootstrapper=new_bootstrapper_name,
            host_address_setting=host_address_setting,
            upgrade_debug=upgrade_debug,
            admin_password=mke_obj.admin_password,
            ucp_id=ucp_id,
            image_list_args=image_list_args,
        )

        # 900 seconds = 15 minutes = the UCP container run timeout
        result = mke_obj.mgr_node.send_docker(command, timeout=900)
        # On larger clusters, UCP upgrade completes, but some of UCP's containers may need
        # a bit of extra time before they are ready. So use wait_for_true() here,
        # but be willing to fail the test if UCP never becomes healthy.
        if not toolbox.common.wait_for_true(
            mke_obj.verify_version,
            UCP_STABILIZATION_TIMEOUT_SECONDS,
            new_bootstrapper_name,
            raise_on_fail=False,
        ):
            raise TestException("Unable to verify UCP version is {}".format(upgrade_tag))
        if not toolbox.common.wait_for_true(
            mke_obj.verify_health,
            UCP_STABILIZATION_TIMEOUT_SECONDS,
            raise_on_fail=False,
        ):
            raise TestException("UCP nodes not healthy following upgrade")
        if result:
            mke_obj.bootstrapper_name = new_bootstrapper_name
            mke_obj.image_list_args = image_list_args
        mke_obj.mgr_node = None
        return result

    def make_fixtures(self):
        """Make related fixtures from a testkit installation.

        Creates:
        --------

        MKE client : if we have manager nodes, then we create an MKE client
            which will then create docker and kubernestes clients if they are
            appropriate.

        MSR Client : if we have an MSR node, then the related client is
            created.

        """

        instance_id = f"{self._instance_id}-{METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID}"
        arguments["hosts"] = self._hosts
        if "accesspoint" in arguments and arguments["accesspoint"]:
            arguments["accesspoint"] = clean_accesspoint(arguments["accesspoint"])

        logger.debug("MKE Provisioner is creating an MKE client plugin: %s", instance_id)
        fixture = self._environment.add_fixture(
            plugin_id=METTA_MIRANTIS_CLIENT_MKE_PLUGIN_ID,
            instance_id=instance_id,
            priority=70,
            arguments=arguments,
            labels={
                "parent_plugin_id": METTA_MIRANTIS_PROVISIONER_MKE_PLUGIN_ID,
                "parent_instance_id": self._instance_id,
            },
            replace_existing=True,
        )
        self.fixtures.add(fixture, replace_existing=True)

        # We got an MKE client, so let's activate it.
        fixture.plugin.api_get_bundle(force=True)
        fixture.plugin.make_bundle_clients()


def clean_accesspoint(accesspoint: str) -> str:
    """Remove any https:// and end / from an accesspoint."""
    accesspoint = accesspoint.replace("https://", "")
    return accesspoint
