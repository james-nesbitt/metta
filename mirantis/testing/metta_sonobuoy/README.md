# METTA Sonobuoy

Use a Suonobuoy workload plugin to get CNCF conformance data out of your cluster

## Usage:

You'll need the following:

1. There must be a kubeapi client avaialble to get a KUBECONFIG from,
   (we can find a way around that, it jsut matched my first usecase)
2. config your plugin with needed info:

fixtures.yml
```
# cncf :: metta.plugin.workload:
cncf:
    plugin_type: workload
    plugin_id: metta_sonobuoy_workload

    # build the plugin from this config, by passing this label/base to it
    from_config: true

    mode: certified-conformance

    kubernetes:
        version: v1.20.1

    plugin:
        plugins:
        - e2e
        envs:
        - e2e.E2E_EXTRA_ARGS=--non-blocking-taints=com.docker.ucp.manager

```

### Use your workload in code

Now your workload plugin can be accessed and used:

```
    cncf = environment_up.fixtures.get_plugin(
        plugin_type='workload', instance_id='cncf')
    """ cncf workload plugin """

    instance = cncf.create_instance(environment_up.fixtures)

    try:
        # start the CNCF conformance run
        logger.info("Starting sonobuoy run")
        instance.run(wait=True)

        # confirm status?
        status = instance.status()
        if status is Status.FAILED:
          logger.error("Sonobuoy failed")

        results = instance.retrieve()

        plugin_results = results.plugin('e2e')
        if plugin_results.status() in [Status.FAILED]:
            for item in plugin_results:
                logger.error("%s: %s (%s)", plugin_id, item.name,
                             item.meta_file_path()))
```

### Use the workload plugin using the metta cli

There are several metta cli sonobuoy commands.  List them using:

```
$/> metta contrib sonobuoy
```
