apiVersion: launchpad.mirantis.com/mke/v1.3
kind: %{ if msr_count > 0 }mke+msr%{ else }mke%{ endif }

metadata:
  name: ${cluster_name}

spec:
  hosts:
%{ for host in hosts ~}

  - role: ${host.role}
  %{ if can( host.ssh ) }
    ssh:
      address: ${host.ssh.address}
      user: ${host.ssh.user}
      keyPath: ${key_path}
  %{ endif ~}
  %{ if can( host.winrm ) }
    winRM:
      address: ${host.winrm.address}
      user: ${host.winrm.user}
      password: ${host.winrm.password}
      useHTTPS: ${host.winrm.useHTTPS}
      insecure: ${host.winrm.insecure}
  %{ endif ~}

  %{ if can( host.hooks ) }
    hooks:
      apply:
    %{ if can( host.hooks.apply.before ) }
        before: %{ for hook in host.hooks.apply.before }
        - "${hook}"%{ endfor }
    %{ endif ~}
    %{ if can( host.hooks.apply.after) }
        after: %{ for hook in host.hooks.apply.after }
        - "${hook}"%{ endfor }
    %{ endif ~}
  %{ endif ~}
%{ endfor ~}

  mcr:
    version: ${mcr_version}
    repoURL: ${mcr_repoURL}
    installURLLinux: ${mcr_installURLLinux}
    installURLWindows: ${mcr_installURLWindows}
    channel: ${mcr_channel}

  mke:
    version: ${mke_version}
    imageRepo: ${mke_image_repo}
    adminUsername: ${mke_admin_username}
    adminPassword: ${mke_admin_password}
    installFlags:
    - "--san=${mke_san}"
    %{ if mke_kube_orchestration }- "--default-node-orchestrator=kubernetes"%{ endif }
    %{ for installFlag in mke_installFlags }
    - "${installFlag}"%{ endfor ~}

    upgradeFlags:
    - "--force-recent-backup"
    - "--force-minimums"%{ for upgradeFlag in mke_upgradeFlags }
    - "${upgradeFlag}"%{ endfor ~}

%{ if msr_count > 0 }
  msr:
    version: ${msr_version}
    imageRepo: ${msr_image_repo}
    installFlags:
    %{ for installFlag in msr_installFlags }
    - "${installFlag}"%{ endfor ~}

    replicaIDs: ${msr_replica_config}
%{ else }
  # No MSR nodes configured
%{ endif }

  cluster:
    prune: %{ if cluster_prune }true%{ else }false%{ endif }
