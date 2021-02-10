#!/bin/bash

timestamp() {
    echo "[INFO] $(date -u "+%Y-%m-%dT%H:%M:%SZ") \"$1\""
}

timestamp "Starting upgrade run"

timestamp "Prep cluster.yaml"

yq w -i cluster.yaml 'spec.ucp.version' 3.3.2

timestamp "Pre cluster.yaml complete"

timestamp "Launchpad begin run"

launchpad apply

timestamp "Launchpad end run"

timestamp "Upgrade run complete"
