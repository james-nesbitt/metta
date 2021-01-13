# Launchpad

(Internal test engineering version)

## What is it

This is based off the MCC (upstream Launchpad repo) of Launchpad, in particular the Terraform configuration files [located here](https://github.com/Mirantis/mcc/tree/master/examples/tf-aws).

The updates in this directory afford the user the ability to select between various OS platforms, namely:

* RHEL: 7.5, 7.6, 7.7, 7.8,8.0, 8.1, 8.2
* CentOS: 7.7, 8.1
* Ubuntu: 16.04, 18.04, 20.04
* SLES: 12 SP4, 15

as well as being able to select from a group of AMIs (currently `public` vs `mirantis`).

**Note:** Just because the Terraform config supports it and builds it out, does _not_ mean that Launchpad will support it. But they've been added today, as a forward-looking optimism. As of this writing, SLES deployments and Ubuntu 20.04 are not yet supported by Launchpad.

## How do I use it

While it would be helpful to be familiar with [the steps provided in the MCC repository](https://github.com/Mirantis/mcc/blob/master/examples/tf-aws/README.md), here's what you need to know for this repo:

### Prerequisites

* Terraform executable
  * Mac users can just use Homebrew: `brew install terraform`
  * everyone can [download from here](https://www.terraform.io/downloads.html)

* `yq` executable
  * Mac users: `brew install yq`
  * instructions for all platforms [are listed here](https://github.com/mikefarah/yq/blob/master/README.md)

* Ansible (optional, but recommended)
  * [Setup instructions from elsewhere in this repo](../system_test_toolbox/ansible)

* AWS credentials
  * if a command such as `aws ec2 describe-instances` is successful (doesn't throw an authentication error) then you should be good to go

### Deploy

* `terraform.tfvars`
  * the main config file - this should be the first and likely only file you need to edit (based off `terraform.tfvars.example`):

    ```text
    manager_count                  = 1
    worker_count                   = 3
    dtr_count                      = 0
    windows_worker_count           = 0
    admin_password                 = "abcd1234changeme"
    windows_administrator_password = "tfaws,,CHANGEME..Example"
    platform                       = "rhel_7.8"
    username                       = "alex"
    task_name                      = "ostrich"
    project                        = "ST-SZNG"
    expire_duration                = "72h"
    engine_version                 = "19.03.12"
    ucp_version                    = "3.3.3"
    kube_orchestration             = true
    dtr_version                    = "2.8.3"
    dtr_install_flags              = ["--ucp-insecure-tls"]
    platform_repo                  = "public"
    ```

  * **Notes:**
    * `windows_administrator_password` tends to be finicky; if you're experiencing Windows deployment issues, start here (and ask the team)
    * `platform_name` popular choices include `rhel_8.2`, `rhel_7.8`, `ubuntu_18.04` - to see the full list, review `platforms.auto.tfvars.json`

* `main.tf`
  * located in the top-level dir (not in the `modules` subdirs)
  * edit this only if you're not using the included shell scripts or the variants described below

* `variables.tf`
  * Contains all of the requisite inputs for the root module
  * If you're not sure what variables you can set in `terraform.tfvars`, review (**DO NOT EDIT**) `variables.tf` for inspiration

* **Any** file ending in `.tf` will be seen by Terraform, so be mindful of any extra files you create in the root or any of the directories referenced by the root `*.tf` files

* deployment script `deploy.sh` will do the right thing based on the above

### Teardown

* `terraform destroy -auto-approve`
  * this is the "I'm done and I know what I'm doing here" approach, so make sure you're in the right directory before kicking it off

## Try it out

As long as you have the prerequisites installed, try running this command:

```bash
./deploy.sh
```

## Tips and tricks

### Making edits to Terraform configs

While making changes, don't spend time fussing over any crufty formatting, as Terraform has a nice helper feature for that.

At any time after making changes to any Terraform config files, run the following to tidy up the formatting (from the config root dir):

```bash
terraform fmt -write=false -recursive -diff
```

Most times you can probably just skip the `-write=false` and just let `fmt` DTRT:

```bash
terraform fmt -recursive -diff
```

If you don't even want to see the diff output (ie, quiet mode), drop the `-diff` as well.

You can run the `fmt` as often as you like. You can save it for the last step before doing your commit, if you prefer. This is purely for human readability.
