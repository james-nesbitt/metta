#!/bin/bash

timestamp() {
    echo "[INFO] $(date -u "+%Y-%m-%dT%H:%M:%SZ") \"$1\""
}

timestamp "Starting prune run"

timestamp "Launchpad begin prune"

launchpad apply --prune

timestamp "Launchpad end prune"

timestamp "Test prune complete"
