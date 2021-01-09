
import os

def mtt_bootstrap(config):
    """ bootstrap the passed toolbox config for mtt common functionality """
    config.sources.add_filepath_source(os.path.dirname(os.path.realpath(__file__)), "mtt_common", 60)
