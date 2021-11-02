# Bootstrapping MKE cluster on Azure

This directory provides an example flow for using Mirantis Launchpad with Terraform and Azure.

## Prerequisites

* An account and credentials for Azure.
* Terraform [installed](https://learn.hashicorp.com/terraform/getting-started/install)
* The Terraform `azurerm` provider requires a number of environment variables to be set. Please refer to the [Terraform Azure Provider](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs) documentation for more details. The minimum required environment variables for this example are:

  * ARM_CLIENT_ID
  * ARM_CLIENT_SECRET
  * ARM_SUBSCRIPTION_ID
  * ARM_TENANT_ID

## Steps

1. Create terraform.tfvars file with needed details. You can use the provided terraform.tfvars.example as a baseline.
2. `terraform init`
3. `terraform apply`
4. `terraform output mke_cluster | launchpad apply --config -`

## Notes

1. If any Windows workers are created then a random password will be generated for the admin account `DockerAdmin` that is created.
2. Only Linux workers are added to the LoadBalancer created for workers.
3. Both RDP and WinRM ports are opened for Windows workers.
4. A default storage account is created for kubernetes.
5. The number of Fault & Update Domains varies depending on which Azure Region you're using. A list can be found [here](https://github.com/MicrosoftDocs/azure-docs/blob/master/includes/managed-disks-common-fault-domain-region-list.md). The Fault & Update Domain values are used in the Availability Set definitions
6. Windows worker nodes may be rebooted after engine install
