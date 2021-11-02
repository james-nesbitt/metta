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
