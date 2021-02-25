# Output plugins

Output plugins are meant to be abvstracted containers to allow sharing of
information between other plugins.
This encapsulation allows decoupling of provider of output and consumer of it
where output data can be abstracted.

## Common output plugins

### Dict

The Dict output contains a dict of data that can be treated as a confiergus
loaded config.  This allows deep retrieval, validation and formatting.

### test

A simple dict that can be used to pass any serializable or string message.
