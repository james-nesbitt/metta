# Dymmy demo

This is a demo of running mtt with a dummy system.  It models the interface but
does not run any cluster management functionality.
The config object is fully active and tested.

PyTest fixtures are defined inline just to keep it simple

## Running this

You will need:

1. install pytest
2. get myy

MTT can be installed using various methods
```
# pip global install (NOT YET REGISTERED)
pip install mtt

# OR pip install from a cloned/downloaded mtt
pip install -e path/to/mtt
```

now just run pytest

```
pytest -s
```
