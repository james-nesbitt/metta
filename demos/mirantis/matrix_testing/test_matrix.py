
import logging
import time

from mirantis.testing.mtt_mirantis.matrix import MatrixRun

logger = logging.getLogger('test_matrix')

@MatrixRun(platforms=['public/rhel/7.9', 'public/rhel/8.3', 'public/ubuntu/18.04'],
    releases=['patch/202012', 'patch/202012'],
    clusters=['poc'])
def test_matrix(config, provisioner):
    """ Matrix permutation test """
    global logger

    variables_config = config.load('variables')
    terraform_config = config.load('terraform')

    id = variables_config.get('id')
    logger = logger.getChild(id)
    logger.info('STARTING')

    # mtt_mirantis_config = config.load('mtt_mirantis')
    # platform = mtt_mirantis_config.get('platform')
    # release = mtt_mirantis_config.get('release')
    # cluster = mtt_mirantis_config.get('cluster')
    # logger.info('presets: %s|%s|%s|%s', variation, platform, release, cluster)




    # logger.info("Getting K8s client")
    # kubectl_client = provisioner.get_client("mtt_kubernetes")
    #
    # coreV1 = kubectl_client.get_CoreV1Api_client()
    # ns = coreV1.read_namespace(name="kube-system")
    # print("NS: {}".format(ns))
    #
    # assert ns.metadata.name == "kube-system", "Wrong namespace given"
