"""

Basic plugin functionality testing

Usage
-----

Should be run using pytest:
```
$/> pytest
```

@NOTE this test needs to test some aspects of the installation of the packages
  and therefor cannot simply use relative aspects of the system.

  YOU MUST INSTALL THE PACKAGES BEFORE RUNNING THE TESTS

@NOTE this is not the right way to load plugins in actual use, but rather is
    just a functional test of the plumbing.  You should always rely on a toolbox
    instance to load a plugin for you

"""

import pytest
from ... import toolbox
from ..plugin import PluginType

@pytest.fixture()
def dummy_conf():
    """ provide a config object for testing plugins

    @TODO we don't actually use the tmp_path and might be able to use
       either a dummy string or a tests specific config path

    """
    sources = toolbox.new_sources()
    sources.add_dict_source({}, "dummy")
    return toolbox.config_from_source_list(sources)

@pytest.fixture()
def dummy_provisioner(dummy_conf):
    """ get the dummy provisioner (use the dummy conf)"""
    return toolbox.get_plugin(PluginType.PROVISIONER, "dummy", dummy_conf)

def test_dummyplugins(dummy_provisioner):
    """ test that we can load some dummy plugins """
    assert dummy_provisioner is not None, "Invalid return when trying to load the dummy provisioner plugin"
