#!/bin/bash

timestamp() {
    echo "[INFO] $(date -u "+%Y-%m-%dT%H:%M:%SZ") \"$1\""
}

timestamp "Starting test run"

timestamp "Terraform initialization"
terraform init
timestamp "Terraform initialization complete"

timestamp "Terraform apply"
terraform apply -auto-approve
timestamp "Terraform apply complete"

timestamp "Create cluster.yaml file from Terraform config"
terraform output -json | yq r --prettyPrint - ucp_cluster.value > launchpad.yaml


timestamp "Create nodes.yaml file from Terraform config"
terraform output -json | yq r --prettyPrint - _ucp_cluster.value > nodes.yaml

timestamp "Create Ansible inventory file"
hosts_tmp="hosts.tmp"
hosts_ini="hosts.ini"
terraform output -json | \
    jq '.ucp_cluster.value.spec.hosts[] | (select(.ssh.user)) | (.role, .ssh.user, .address, .ssh.keyPath)' -r | \
    paste - - - - | \
    awk '{print $1, "ansible_host="$2"@"$3, "ansible_ssh_private_key_file="$4}' > ${hosts_tmp}

# expropriate first worker node for use as loadtester
gsed -i "0,/^worker /s//loadtester /" ${hosts_tmp}

roles="manager worker dtr loadtester"

for role in ${roles}; do
    echo "[${role}s]"
    awk 'BEGIN {c=0} ; /^'"${role}"'/ {c++ ; $1=$1c; print}' ${hosts_tmp}
    echo
done > ${hosts_ini}

cat << EOF >> ${hosts_ini}
[cluster:children]
managers
workers
dtrs
EOF

timestamp "Launchpad begin run"
launchpad -d apply
timestamp "Test run complete"
