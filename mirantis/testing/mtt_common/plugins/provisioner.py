"""

A mock provisioner to act as a backend when the cluster is already provisioned

"""

import yaml
import json
import re
import logging
import os.path
import mirantis.testing.mtt as mtt
import mirantis.testing.mtt_common as mtt_common
from mirantis.testing.mtt.provisioner import ProvisionerBase

logger = logging.getLogger("mirantis.testing.mtt_common.provisioner.existing")

MTT_COMMON_PROVISIONER_EXISTING_CONFIG_KEY_OUTPUTS = 'outputs'
""" what Config.load('provisioner').get(KEY) do we use to get a list of outputs for an existing system """
MTT_COMMON_PROVISIONER_EXISTING_CONFIG_KEY_CLIENTS = 'clients'
""" what Config.load('provisioner').get(KEY) do we use to get a list of clients for an existing system """
MTT_COMMON_PROVISIONER_EXISTING_REGEX_OUTPUT_IS_A_FILE = r'^file:(?P<file>[\/~\w]*\.(json|yaml|yml))$'
""" Default regex pattern used to string template, which needs to identify if an output value is a file """

class ExistingBackendProvisionerPlugin(ProvisionerBase):
    """ Existing backend provisioner

    This provisioner assumes that all cluster resources are active and in place
    and so no actual management is needed.

    The provisioner provides clients only based on passed in values. The provisioner
    pretends to manage a system, and then provides interaction components such as
    output and clients based on configuration

    """

    """ MOCK cluster management """

    def prepare(self):
        """ Prepare the provisioner

        For this provisioner what we do is parse the collected config for the
        existing backend and try to interpret it into a list of outputs and
        clients.
        For most cases of running against an existing cluster, this is all you
        need, and all you want.

        You will need to get the client and output data into the configuration
        for the provisioner (where you set the plugin id) which you can do from
        any config source plugin such as a flat file, or a Dict.

        """
        provisioner_config = self.config.load(mtt.MTT_PROVISIONER_CONFIG_LABEL_DEFAULT)
        output_data = provisioner_config.get(MTT_COMMON_PROVISIONER_EXISTING_CONFIG_KEY_OUTPUTS)
        client_data = provisioner_config.get(MTT_COMMON_PROVISIONER_EXISTING_CONFIG_KEY_CLIENTS)

        self.outputs = output_data

        # Modify the config object, and add our clients, but to a custom label just for us
        self.clients_label = "{}_clients".format(self.instance_id)
        client_data = {
            self.clients_label: {
                mtt.MTT_CLIENT_CONFIG_KEY_CLIENTS: client_data
            }
        }
        self.config.add_source(mtt_common.MTT_PLUGIN_ID_CONFIGSOURCE_DICT, self.clients_label).set_data(client_data)

        self.clients = mtt.new_clients_from_config(self.config, self.clients_label)

    def up(self):
        pass

    def down(self):
        pass

    def output(self, output_id: str):
        """ Return our mock output name

        if we have an output key stored in the mock output then return it.

        if the output value matches our regex indicating that it is pointing to
        a yaml/json file then return the parsed data.

        We do not keep the parsed data, and will parse it again on the next request

        """
        if output_id in self.outputs:
            output = self.outputs[output_id]
            match = re.match(MTT_COMMON_PROVISIONER_EXISTING_REGEX_OUTPUT_IS_A_FILE, output)
            if match is not None:
                file = match.group('file')
                extension = os.path.splitext(file)[1].lower()
                file_output = ''
                with open(file) as matching_file:
                    if extension == ".json":
                        try:
                            file_output = json.load(matching_file)
                        except json.decoder.JSONDecodeError as e:
                            raise ValueError("Failed to parse one of the config files '{}': {}".format(matching_file, e))
                    elif extension == ".yml" or extension == ".yaml":
                        try:
                            file_output = yaml.load(matching_file, Loader=yaml.FullLoader)
                        except yaml.YAMLError as e:
                            raise ValueError("Failed to parse the output file '{}': {}".format(matching_file, e))
                    else:
                        raise ValueError("told to load '{}}', but could not intepret its extension".format(matching_file))

                assert file_output, "Empty output from {}".format(matching_file)
                return file_output
            else:
                return output

        raise KeyError("Existing provisioner plugin was not given the requested output: %s", output_id)

    def get_client(self, client_id: str):
        """ Create clients from the mock client configuration """

        if client_id in self.clients:
            return self.clients[client_id]

        raise KeyError("Existing provisioner plugin was not given the requested output: %s", client_id)
