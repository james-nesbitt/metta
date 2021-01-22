
from mirantis.testing.mtt import plugin as mtt_plugin
from mirantis.testing.mtt.config import Config

from .plugins.provisioner import TerraformProvisionerPlugin

MTT_TERRAFORM_PROVISIONER_PLUGIN_ID = 'mtt_terraform'
""" Terraform provisioner plugin id """

""" provisioner plugin_id for the mtt dummy plugin """
@mtt_plugin.Factory(type=mtt_plugin.Type.PROVISIONER, plugin_id=MTT_TERRAFORM_PROVISIONER_PLUGIN_ID)
def mtt_plugin_factory_provisioner_terraform(config: Config, instance_id: str = ''):
    """ create an mtt provisionersss dict plugin """
    return TerraformProvisionerPlugin(config, instance_id)
