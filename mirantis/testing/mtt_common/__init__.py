
import os

def mtt_common_bootstrap(config):
    """ bootstrap the passed toolbox config for mtt common functionality """
    mtt_common_path = os.path.dirname(os.path.realpath(__file__))
    mtt_common_config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "config")
    config.sources.add_filepath_source(mtt_common_config_path, "mtt_common", 60)
    config.sources.add_filepath_source(mtt_common_path, "mtt_common_root", 60)
