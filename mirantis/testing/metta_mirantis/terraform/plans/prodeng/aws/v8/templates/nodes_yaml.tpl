%{ for host in hosts ~}
- role: ${host.role}
  address: ${host.instance.public_ip}
  privateIp: ${host.instance.private_ip}
%{ if can( host.ssh ) }
  ssh:
    address: ${host.ssh.address}
    user: ${host.ssh.user}
    keyPath: ${key_path}
%{ endif ~}
%{ if can(host.winrm) }
  winRM:
    address: ${host.instance.public_ip}
    user: ${host.winrm.user}
    password: ${host.winrm.password}
    useHTTPS: ${host.winrm.useHTTPS}
    insecure: ${host.winrm.insecure}
%{ endif ~}

%{ endfor ~}
