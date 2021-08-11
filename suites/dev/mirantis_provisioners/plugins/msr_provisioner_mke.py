"""

Provisioner plugin for installing MSR.

Installs MSR with access to a set of hosts with MKE installed and
executable capacity (SSH/WinRM.)

"""

METTA_MIRANTIS_PROVISIONER_MSR_PLUGIN_ID = "mirantis_msr_provisioner"
""" Mirantis MKE API Provisioner plugin id """


METTA_MIRANTIS_MSR_CONFIG_LABEL = "msr"
"""Configerus load() label for finding MSR provisioner configuration."""


class MSRProvisionerPlugin:
    """MSR Installer provisioner plugin."""

    # pylint: disable=too-many-arguments
    # pylint: disable=no-self-use
    def _install_msr(self):
        """Install DTR."""
        new_nodes = dtr_obj.select_dtr_nodes(num_dtr_replicas)
        dtr_obj.dtr_nodes.extend(new_nodes)

        dtr_obj.bootstrapper_name = toolbox.common.get_dtr_bootstrapper_name(hub_repo, hub_tag)
        dtr_obj.pull_dtr_images(new_nodes, dtr_obj.bootstrapper_name)

        dtr_node = new_nodes.pop(0)
        log("Installing DTR '{0}' on node {1}".format(dtr_obj.bootstrapper_name, dtr_node.hostname))

        # to enable debug for the install.
        # install_debug = '--debug'
        install_debug = ""

        # The UCP URL including domain and port
        dtr_obj.ucp_url = "https://{}".format(ucp_dns_address)

        # ucp-node: node where DTR is being installed
        # The hostname of the cluster node to deploy DTR. Random by default.
        # You can find the hostnames of the nodes in the cluster in the UCP web interface,
        # or by running docker node ls on a UCP manager node.
        node_hostname = dtr_node.hostname

        # dtr-external-url
        # URL of the host or load balancer clients use to reach DTR. When you use this flag,
        # users are redirected to UCP for logging in. Once authenticated they are redirected
        # to the URL you specify in this flag. If you don’t use this flag, DTR is deployed
        # without single sign-on with UCP. Users and teams are shared but users log in separately
        # into the two applications. You can enable and disable single sign-on within your DTR
        # system settings. Format https://host[:port], where port is the value you used with
        # --replica-https-port.
        dtr_ip = dtr_node.public_ip

        # replica settings
        # Assign a 12-character hexadecimal ID to the DTR replica. Random by default.
        replica_settings = "--replica-id {}".format(dtr_obj.replica_id)

        # Disable TLS verification for UCP. The installation uses TLS but always trusts the TLS
        # certificate used by UCP, which can lead to MITM (man-in-the-middle) attacks.
        # For production deployments, use --ucp-ca "$(cat ca.pem)" instead.
        ucp_insecure_tls = "--ucp-insecure-tls"

        command = (
            "docker run --rm --name dtr "
            "{bootstrapper} "
            "install "
            "{install_debug} "
            "--ucp-url '{ucp_url}' "
            "--ucp-node '{node_hostname}' "
            "--dtr-external-url '{dtr_ip}' "
            "--ucp-username admin "
            "--ucp-password '{admin_password}' "
            "{replica_settings} "
            "{ucp_insecure_tls} "
        ).format(
            bootstrapper=dtr_obj.bootstrapper_name,
            install_debug=install_debug,
            ucp_url=dtr_obj.ucp_url,
            node_hostname=node_hostname,
            dtr_ip=dtr_ip,
            admin_password=dtr_obj.ucp_admin_password,
            replica_settings=replica_settings,
            ucp_insecure_tls=ucp_insecure_tls,
        )

        result = dtr_node.send_docker(command, timeout=720)
        users.configure_for_dtr(dtr_obj.dns_address)
        time.sleep(15)
        dtr_obj.verify_version(dtr_obj.bootstrapper_name)
        dtr_obj.verify_health()
        dtr_obj.cluster.set_dtr_node(dtr_node)
        if result:
            log("Installed DTR Version {0} on node {1}".format(dtr_obj.version, dtr_node.hostname))
        return result

    def _upgrade_msr(self):
        """Upgrade DTR. Will pull the images as well as perform the upgrade."""
        new_bootstrapper_name = toolbox.common.get_dtr_bootstrapper_name(upgrade_repo, upgrade_tag)
        dtr_node = msr_obj.dtr_nodes[0]

        if msr_obj.verify_version(new_bootstrapper_name, raise_on_fail=False):
            log("DTR already at version {}. Skipping.".format(new_bootstrapper_name))
            return None
        log("pulling DTR image with tag {0}".format(upgrade_tag), "DEBUG")
        msr_obj.pull_dtr_images(msr_obj.dtr_nodes, new_bootstrapper_name)

        upgrade_debug = ""
        # Disable TLS verification for UCP. The installation uses TLS but always trusts the TLS
        # certificate used by UCP, which can lead to MITM (man-in-the-middle) attacks.
        # For production deployments, use --ucp-ca "$(cat ca.pem)" instead.
        ucp_insecure_tls = "--ucp-insecure-tls"

        command = (
            "docker run --rm --name dtr "
            "{bootstrapper} "
            "upgrade "
            "{debug} "
            "--existing-replica-id={replica_id} "
            "--ucp-url '{ucp_url}' "
            "--ucp-username=admin "
            "--ucp-password='{admin_password}' "
            "{ucp_insecure_tls} "
        ).format(
            bootstrapper=new_bootstrapper_name,
            debug=upgrade_debug,
            replica_id=msr_obj.replica_id,
            ucp_url=msr_obj.ucp_url,
            admin_password=msr_obj.ucp_admin_password,
            ucp_insecure_tls=ucp_insecure_tls,
        )
        result = dtr_node.send_docker(command, timeout=720)
        msr_obj.verify_version(new_bootstrapper_name)
        msr_obj.verify_health()
        return result
