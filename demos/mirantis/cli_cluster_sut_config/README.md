# Cluster / SUT Overriding Configuration

A demo on how to use the overriding/overloading features of the config handler
to get adaptability in your test harness.

This approach preaches some patterns but attempts to be readable enough that
it can be interpreted for different approaches.

That module actually has a very similar system to this override approach referred
to as the ltc variation.  There is another demo of the ltc approach which shows
how you can use the same ideas here but with suts/clusters defined by mirantis
that relate to our releases and our test cluster definitions.

## Configuration overrides

### Cluster definition

Different cluster definition folders contain config overrides that change the
cluster definition.

1. poc : man:1, worker:3
2. small_business: man:3, worker: 20
3. data_center : man:5, worker:100

(these are not official values, I just picked something that made some sense)

POC is default. There is a pytest option added to select a cluster:

```
pytest --cluster small_business
```

### System Under Test

Different Mirantis cloud versions can be installed

1. 202101 : the patch released in 2021 Jan
1. 202012 : the patch released in 2020 Dec

202101 is Default.  There is a pytest options to select a different sut:

(this is demo data, and may not represent actual values)

```
pytest --sut 202012
```

## The terraform plan

This demo uses the PRODENG terraform plan in the mtt_mirantis module.

We use that plan/graph only so that we don't have to include redundant terraform
here, allowing us to focus on using config overrides functionally.
