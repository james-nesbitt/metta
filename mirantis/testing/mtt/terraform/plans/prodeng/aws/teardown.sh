#!/bin/bash

timestamp() {
    echo "[INFO] $(date -u "+%Y-%m-%dT%H:%M:%SZ") \"$1\""
}

timestamp "Starting test run"

timestamp "Launchpad reset"

launchpad reset

timestamp "Launchpad reset complete"

timestamp "Terraform destroy"

terraform destroy -auto-approve

timestamp "Terraform destroy complete"

timestamp "Test run complete"
