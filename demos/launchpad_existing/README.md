# Existing cluster demo

This is a demo of running mtt against an existing cluster using launchpad to
install.

Here you are are expected to have a launchpad.yml file ready, and relevant keys
accessible as defined in the launchpad.yml

## Running this

You will need:

1. install pytest and launchpad
2. get mtt
3. have a good launchpad yml file ready, be default `./launchpad.yml`

**people often forget that launchpad.yml often contains relative ssh key paths**

MTT can be installed using various methods
```
# pip global install (NOT YET REGISTERED)
pip install mtt

# OR pip install from a cloned/downloaded mtt
pip install -e path/to/mtt
```

now just run pytest (with -s to see launchpad output)

```
pytest -s
```
