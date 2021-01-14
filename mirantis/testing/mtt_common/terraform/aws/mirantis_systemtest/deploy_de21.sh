#!/bin/bash

timestamp() {
    echo "[INFO] $(date -u "+%Y-%m-%dT%H:%M:%SZ") \"$1\""
}

timestamp "Starting test run"

timestamp "Initializing main.tf"
cp main.tf.de21 main.tf

timestamp "Terraform initialization"
terraform init
timestamp "Terraform initialization complete"

timestamp "Terraform apply"
terraform apply -auto-approve
timestamp "Terraform apply complete"

timestamp "Create cluster.yaml file from Terraform config"
terraform output -json | yq r --prettyPrint - ucp_cluster.value > cluster.yaml

timestamp "Create Ansible inventory file"
terraform output -json | \
    jq '.ucp_cluster.value.spec.hosts[] | (select(.ssh.user)) | (.ssh.user, .address, .ssh.keyPath)' -r | \
    paste - - - | \
    awk '{print $1"@"$2, "ansible_ssh_private_key_file="$3}' > hosts

# timestamp "Run Ansible play to prep RHEL targets"
# ansible-playbook prep_rhel.yml
# timestamp "Ansible play complete"

timestamp "Launchpad begin run"
launchpad -d apply
timestamp "Launchpad end run"

timestamp "Test run complete"
