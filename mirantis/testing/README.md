# Mirantis Testing

Testing components

Some of the packages are here for convenience but could be easily exported to
their own distributions.

## Toolbox

The toolbox forms the functional core of MTT focusing on the following:

1. Config management
2. Interacting with other packages and loading their plugins
3. Specific plugin type generation, such as provisioner

Most of the functionality is meant to be used directly from the __init__ methods
which are written to be directly interpreted.

### Config

The config handler is its own beast.  it is more complicated than it needs to be
but it delivers good features because of that.

## Vendor plugins

Vendor plugins provide functionality related to 3rd party tools

Of note are

### MTT Terraform

Provisioning based on terraform plans

### MTT Launchpad

Installing Mirantis products onto a cluster provisioned by another profivisioner

### MTT Kubernetes  

Client interactions for Kubernetes

### MTT Docker

Client interactions for Docker servers

### MTT Common

A set of common resources that can be used for any test system.  This allows
Mirantis to distribute things like terraform plans and workloads that we use
when we test the products
