# Cluster/Platform/Release Overriding Configuration

A demo on how to use the overriding/overloading features of configerus an
pytest cli options to get run time adapatbility in your test harness
to get adaptability in your test harness.

This approach preaches some patterns but attempts to be simple enough that it is
easy to consumer.
It can be hard to read, as it relies heavily on the MTT_Mirantis preset concept
which allows us to use values that mtt_mirantis correlates with whole sets of
configuration for things like cluster definition, os platform and product
release versions.  Best to look first at mtt_mirantis.presets to see how it
detects presets, and also look in mtt_mirantis/config for the cluster, release
and platfom preset configuration folders.

## Configuration overrides

### Cluster definition

In conftest we add a cli option for each of the mtt_mirantis presets, that can
be used at runtime to alter the nature of the testing cluster.

At the time of writing, the following presets were available:

--cluster : how big a cluster and how many of different types of nodes;
--release : which mirantis products to install;
--platform : which OS platforms to use for the testing cluster.

The values have to be valid according to mtt_mirantis or an exception will be
raised.

## The terraform plan

This demo uses the PRODENG terraform plan in the mtt_mirantis module.

That terraform plan is quite complex, but we use that plan/graph only so that
we don't have to include redundant terraform here, allowing us to focus on using
config overrides functionally.
