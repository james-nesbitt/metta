#!/bin/bash

# DE version = (engine ucp dtr dtr_imageRepo)
DE31=("19.03.12" "3.3.2" "2.8.2" "docker.io/mirantis")
DE30=("19.03.5" "3.2.7" "2.7.4" "docker.io/docker")

CLUSTER_FILE="cluster.yaml"

timestamp() {
    echo "[INFO] $(date -u "+%Y-%m-%dT%H:%M:%SZ") \"$1\""
}

upgrade_cluster(){
    ENGINE_VER=$1
    UCP_VER=$2
    DTR_VER=$3
    DTR_IMAGE_REPO=$4

    timestamp "Starting upgrade run - versions: ${ENGINE_VER} ${UCP_VER} ${DTR_VER} ${DTR_IMAGE_REPO}"

    timestamp "Prep ${CLUSTER_FILE}"

    yq w -i ${CLUSTER_FILE} 'spec.engine.version' ${ENGINE_VER}
    yq w -i ${CLUSTER_FILE} 'spec.ucp.version' ${UCP_VER}
    yq w -i ${CLUSTER_FILE} 'spec.dtr.version' ${DTR_VER}
    yq w -i ${CLUSTER_FILE} 'spec.dtr.imageRepo' ${DTR_IMAGE_REPO}

    timestamp "Prep ${CLUSTER_FILE} complete"

    timestamp "Launchpad begin run"
    launchpad -d apply
    timestamp "Launchpad end run"

    timestamp "Upgrade run complete - versions: ${ENGINE_VER} ${UCP_VER} ${DTR_VER} ${DTR_IMAGE_REPO}"
}

upgrade_cluster ${DE30[@]}

timestamp "Sleeping for 120s to allow the upgrade just completed to quiesce..."
sleep 120

upgrade_cluster ${DE31[@]}
