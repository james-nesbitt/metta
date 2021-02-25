
import logging
import itertools
from typing import List
from threading import Thread

from mirantis.testing.metta.environment import Environment

from .preset import combination_config

logger = logging.getLogger("metta_mirantis.matrix")


class MatrixRun:
    """ Matrix decorator that will run a method for all matrix combinations

    Expects to decorate a method: func(config:Config, provisioner)

    """

    def __init__(self, platforms: List[str] = [],
                 clusters: List[str] = [], releases: List[str] = []):
        """ register the decoration """
        logger.debug("MatrixTestRun")

        self.matrix = list(itertools.product(*[
            platforms,
            clusters,
            releases
        ]))

    def __call__(self, func):
        """ call the decorated function

        Returns:

        wrapped function(config: Config)
        """

        def matrix_wrap(environment: Environment):
            logger.debug("Matrix test run exec")

            variables_config = config.load("variables")

            i = 0
            for combination in self.matrix:

                metta_dict = {}
                if combination[0]:
                    metta_dict["platform"] = combination[0]
                if combination[1]:
                    metta_dict["cluster"] = combination[1]
                if combination[2]:
                    metta_dict["release"] = combination[2]

                id = str("-".join(metta_dict.values())).replace("/", "-")
                logger.debug("MatrixTestRun::Combination: %s", id)

                metta_dict["id"] = "{}-{}".format(
                    variables_config.get("id"), id).replace(
                    "/", "-")

                combination_config = config.copy()
                combination_config.add_source(metta.SOURCE_DICT, "combination", config.default_priority() + 1).set_data({
                    "metta": metta_dict,
                    "variables": {
                        "id": "{}-{}".format(func.__code__.co_name, id).replace("/", "-"),
                        "resource_prefix": "{}-matrix{}".format(func.__code__.co_name, i).replace("/", "-").replace("_", "-")
                    }
                })

                # tell metta to add variation/platform/release/cluster
                add_preset_config(combination_config)
                # build a new metta provisioner now that we have added config
                combination_provisioner = metta.new_provisioner_from_config(
                    combination_config, "matrix_provisioner")

                thread = ProvisionerUpFuncCallThread(
                    id, combination_config, combination_provisioner, func)
                thread.start()

                i += 1

        return matrix_wrap


class ProvisionerUpFuncCallThread(Thread):

    # def __init__(self,id, config, provisioner, func):
    def __init__(self, id, config, provisioner, func):
        self.logger = logger.getChild(
            "{}:matrix:{}".format(
                func.__code__.co_name, id))
        self.id = id
        self.config = config
        self.provisioner = provisioner
        self.func = func

        Thread.__init__(self)

    def run(self):
        self.logger.debug("RUNNING " + self.id)

        conf = self.config.load("config")
        provisioner_config = self.config.load("provisioner")

        try:
            self.logger.info(
                "Preparing the testing cluster using the provisioner")
            self.provisioner.prepare()
        except Exception as e:
            raise Exception("Provisioner failed to prepare()") from e
        try:
            self.logger.info(
                "Starting up the testing cluster using the provisioner")
            self.provisioner.apply()
        except Exception as e:
            raise Exception("Provisioner failed to apply()") from e

        self.func(self.config, self.provisioner)

    def run2(self):
        """ get the provisioner but start the provisioner before returning

        This is preferable to the raw provisioner in cases where you want a running
        cluster so that the cluster startup cost does not get reflected in the
        first test case which uses the fixture.  Also it can tear itself down

        You can still use provisioner.apply() update the resources if the provisioner
        can handle it.
        """
        self.logger.info("Running metta provisioner up()", id)

        conf = self.config.load("config")
        provisioner_config = self.config.load("provisioner")

        try:
            self.logger.info(
                "Preparing the testing cluster using the provisioner")
            self.provisioner.prepare()
        except Exception as e:
            raise Exception("Provisioner failed to prepare()") from e
        try:
            self.logger.info(
                "Starting up the testing cluster using the provisioner")
            self.provisioner.apply()
        except Exception as e:
            raise Exception("Provisioner failed to apply()") from e

        self.func(self.config, self.provisioner)

        if conf.get("options.destroy-on-finish", exception_if_missing=False):
            try:
                self.logger.info(
                    "Stopping the test cluster using the provisioner as directed by config")
                self.provisioner.destroy()
            except Exception as e:
                raise Exception("Provisioner failed to destroy()") from e
        else:
            self.logger.info(
                "Leaving test infrastructure in place on shutdown")
