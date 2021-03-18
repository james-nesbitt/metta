# Launchpad

Install Mirantis products onto your cluster.

## Usage

Launchpad runs using a yaml config file source.  The launchpad plugin requires
a filepath to the filesource.
The provisioner will try to read the source for the launchpad file from config
and write that to file, updating it before running the client.  This may seem
limiting but it allows you to leverage the dynamic aspects of the configuration
system to populate the file.  Because we write the file from fresh config right
before we use it, it can rely on dynamic data sources available at that time.

This gives a few options:

1. `config: "[file:path/to/file.yml]"` : you can pull config from a real yaml
  file.  This allows you to keep the origin yaml in a file, but the provisioner
  will copy it every time it is applied (safe from editing.)
2. `config: "[output:mke_cluster?Null]"` : pull the yaml config from an output
  plugin, which could be a dummy plugin, or a real output created by another
  plugin in operation.
