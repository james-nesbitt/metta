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
  * if a command such as `aws sts get-caller-identity` is successful (doesn't throw an authentication error) then you should be good to go

### Deploy

`terraform` will use variables configured in one or more files, using the loading order [described on this page](https://www.terraform.io/docs/language/values/variables.html#variable-definition-precedence).

A brief recap is as follows:

> Terraform loads variables in the following order, with later sources taking precedence over earlier ones:
>
> * Environment variables
> * The `terraform.tfvars` file, if present.
> * The `terraform.tfvars.json` file, if present.
> * Any `*.auto.tfvars` or `*.auto.tfvars.json` files, processed in lexical order of their filenames.
> * Any `-var` and `-var-file` options on the command line, in the order they are provided. (This includes variables set by a Terraform Cloud workspace.)

If the filename doesn't match the above format, it will get ignored. Other than that, any file ending in `.tf` will be considered as Terraform HCL configuration. Unless a config file specifies a subdirectory (eg, module) to consider, all subdirs will be ignored.

In our case, most of the options you'll want or need to customize will belong in `terraform.tfvars`.

How we use these files:

* `terraform.tfvars`
  * put most/all of your local config options in this file; use `terraform.tfvars.example` for inspiration
  * you might find it preferable to create a separate file named `passwords.auto.tfvars` to hold the password data, eg:

    ```text
    admin_password                 = "abcd1234changeme"
    windows_administrator_password = "tfaws,,CHANGEME..Example"
    ```

**Notes:**

* variables of particular interest:
  * `windows_administrator_password` tends to be finicky; if you're experiencing Windows deployment issues, start here (and ask the team)
  * `platform_name` popular choices include `rhel_8.2`, `rhel_7.8`, `ubuntu_18.04` - to see the full list, review `platforms.auto.tfvars.json` (eg, `jq '.platforms.public | keys' < platforms.auto.tfvars.json` for the public AMIs or `jq '.platforms.mirantis | keys' < platforms.auto.tfvars.json` for the private Mirantis AMIs)
  * `open_sg_for_myip` will add a SG rule which opens up your cluster to all ports/protocols from your IP (and only from your IP), in addition to the other minimalist SG rules; don't use this unless you have a need to access other ports (eg, troubleshooting, accessing a swarm or kube service you've created, etc)

* `variables.tf`
  * Config file with all of the requisite inputs for the root module
  * If you're not sure what variables you can set in `terraform.tfvars`, review (**DO NOT EDIT**) `variables.tf` for inspiration

* `*.tf`
  * these config files provide the configuration logic; don't edit unless you're working on a PR, or need to do a quick local hack
  * the prefixes for files such as `main.tf`, `variables.tf`, `outputs.tf` are arbitrary otherwise, and are named mainly for human convenience

* **Any** file ending in `.tf` will be seen by Terraform, so be mindful of any extra files you create in the root or any of the directories referenced by the root `*.tf` files

* utility script `deploy.sh` will do the right thing based on the above

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
