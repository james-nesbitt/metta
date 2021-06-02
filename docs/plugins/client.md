# Clients

A client plugin interacts with a cluster.  

The nature of the plugin is very closely tied to the nature of the cluster.  As
such a client is typically created by asking a provisioner to produce it.
You can provide all of the config that a client might need to run, if such values
are predictable.

Client plugins are meant to be used either directly in code, or by workload plugins

While the client plugin factory interface for construction is very standard, its
behaviour is completely custom and as such a consumer much know how to use it.
Workload plugins that use clients typically ask for a specific client type and
know how to interact with them

## Design

Clients are anything that the factory function returns, but tend to be objects that
provide access based on their own implementation.

If you ask for a client, you should know what to do with it.
