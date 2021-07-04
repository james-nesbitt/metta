"""

PLUGINS: OUTPUT.

Output plugins define returned content from an operation that can be interacted
with in a predictable manner.  This gives some abstraction to allow coupling
between unknown plugins for passing data or messages.
While the output plugins themselves define their interface, meaning that you
have to know the type of plugin you are consuming, it does allow for a small
number of common intermediate representations along with allowing for an
extensible system.

It is expected that a small number of output plugins can handle most needs.

"""

METTA_PLUGIN_INTERFACE_ROLE_OUTPUT = "output"
""" metta plugin interface identifier for output plugins """

METTA_OUTPUT_CONFIG_OUTPUTS_LABEL = "outputs"
""" A centralized configerus load label for multiple outputs """
METTA_OUTPUT_CONFIG_OUTPUT_LABEL = "output"
""" A centralized configerus load label for an output """
METTA_OUTPUT_CONFIG_OUTPUTS_KEY = "outputs"
""" A centralized configerus key for multiple outputs """
METTA_OUTPUT_CONFIG_OUTPUT_KEY = "output"
""" A centralized configerus key for one output """
