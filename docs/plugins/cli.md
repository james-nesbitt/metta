# CLI Plugins

CLI Plugins give commands to the METTA cli (`mettac`)

## Requirements

Each plugin should have a `fire()` method which analyzes the environment, and
then provides a deep dict of commands and command groups which the cli will
present to the user.

### Introspection methods

These methods should return json (preferred indented) which allow consumer
introspection into aspects of the environment.

### Action methods

Make changes to resource of the cluster.
