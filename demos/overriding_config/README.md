# Overriding Configuration

A demo on how to use the overriding/overloading features of the config handler
to get adaptability in your test harness.

This approach preaches some patterns but attempts to be readable enough that
it can be interpreted for different approaches.

## Cluster definition

Different cluster definition folders contain config overrides that change the
cluster definition.

1. poc : man:1, worker:3
2. small_business: man:3, worker: 20
3. data_center : man:5, worker:100

(these are note official values, I just picked something that made some sense)

POC is default. There is a pytest option added to select a cluster:

```
pytest --cluster small_business
```

## System Under Test

Different Mirantis cloud versions can be installed

1. 202101 : the patch released in 2021 Jan
1. 202012 : the patch released in 2020 Dec

202101 is Default.  There is a pytest options to select a different sut:

```
pytest --sut 202012
```

## TODO

All of these cluster and sut configurations should likely be moved to mtt_common
