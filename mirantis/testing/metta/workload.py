"""

PLUGIN: Output.

Workload plugins use clients to apply workloads to a testing system.  The
system is irrelevant tothe workload plugin, as it only cares whether or not it
can retrieve the expected clients.

Workload clients are expected to allow creation of Workload instances from
clients, so that multiple applications of the workload can be managed at one
time.

"""

METTA_PLUGIN_INTERFACE_ROLE_WORKLOAD = "workload"
""" Metta plugin interface identifier for workloads """

METTA_WORKLOAD_CONFIG_WORKLOADS_LABEL = "workloads"
""" A centralized configerus load label for multiple workloads """
METTA_WORKLOAD_CONFIG_WORKLOAD_LABEL = "workload"
""" A centralized configerus load label for a workload """
METTA_WORKLOAD_CONFIG_WORKLOADS_KEY = "workloads"
""" A centralized configerus key for multiple workloads """
METTA_WORKLOAD_CONFIG_WORKLOAD_KEY = "workload"
""" A centralized configerus key for one workload """
