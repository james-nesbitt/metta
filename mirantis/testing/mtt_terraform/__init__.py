"""

MTT Terraform

MTT contrib functionality for terraform.  Primarily a terraform provisioner
plugin.

"""

from configerus.config import Config

from mirantis.testing.mtt import plugin as mtt_plugin

from .plugins.provisioner import TerraformProvisionerPlugin

MTT_TERRAFORM_PROVISIONER_PLUGIN_ID = 'mtt_terraform'
""" Terraform provisioner plugin id """
@mtt_plugin.Factory(type=mtt_plugin.Type.PROVISIONER, plugin_id=MTT_TERRAFORM_PROVISIONER_PLUGIN_ID)
def mtt_plugin_factory_provisioner_terraform(config:Config, instance_id:str = ''):
    """ create an mtt provisionersss dict plugin """
    return TerraformProvisionerPlugin(config, instance_id)

def configerus_bootstrap(config:Config):
    """ MTT_Terraform configerus bootstrap

    We dont't take any action.  Our purpose is to run the above factory
    decorator to register our plugin.

    """
    pass
