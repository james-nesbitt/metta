#!/bin/bash

timestamp() {
    echo "[INFO] $(date -u "+%Y-%m-%dT%H:%M:%SZ") \"$1\""
}

timestamp "Starting test run"

timestamp "Checking AWS credentials"
AWS_PAGER="" aws sts get-caller-identity > /dev/null
if [ $? -ne 0 ] ; then
    echo "Invalid AWS credentials - exiting"
    exit 1
fi
timestamp "AWS credentials confirmed valid"

timestamp "Terraform initialization"
terraform init
timestamp "Terraform initialization complete"

timestamp "Terraform apply"
terraform apply -auto-approve
timestamp "Terraform apply complete"

timestamp "Create launchpad.yaml file from Terraform config"
terraform output -json "mke_cluster" | yq -y > launchpad.yaml

timestamp "Create nodes.yaml file from Terraform config"
terraform output -json "_mke_cluster" | yq -y > nodes.yaml

timestamp "Create Ansible inventory file"
hosts_tmp="hosts.tmp"
hosts_ini="hosts.ini"
terraform output -json | \
    jq '.mke_cluster.value.spec.hosts[] | (select(.ssh.user)) | (.role, .ssh.user, .address, .ssh.keyPath)' -r | \
    paste - - - - | \
    awk '{print $1, "ansible_host="$2"@"$3, "ansible_ssh_private_key_file="$4}' > ${hosts_tmp}

# expropriate first worker node for use as loadtester
gsed -i "0,/^worker /s//loadtester /" ${hosts_tmp}

roles="manager worker msr loadtester"

for role in ${roles}; do
    echo "[${role}s]"
    awk 'BEGIN {c=0} ; /^'"${role}"'/ {c++ ; $1=$1c; print}' ${hosts_tmp}
    echo
done > ${hosts_ini}

cat << EOF >> ${hosts_ini}
[cluster:children]
managers
workers
msrs
EOF

timestamp "Launchpad begin run"
launchpad -d apply
timestamp "Launchpad end run"

timestamp "Test run complete"
