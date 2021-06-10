[managers]
%{ for idx in mgr_idxs ~}
manager${idx} ansible_host=${user}@${mgr_hosts[idx].instance.public_ip} ansible_ssh_private_key_file=${key_file}
%{ endfor ~}

[workers]
%{ for idx in wkr_idxs ~}
worker${idx} ansible_host=${user}@${wkr_hosts[idx].instance.public_ip} ansible_ssh_private_key_file=${key_file}
%{ endfor ~}

[msrs]
%{ for idx in msr_idxs ~}
msr${idx} ansible_host=${user}@${msr_hosts[idx].instance.public_ip} ansible_ssh_private_key_file=${key_file}
%{ endfor ~}

[cluster:children]
managers
workers
msrs
