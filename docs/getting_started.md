# Getting Started

## 1. Define an environment

MTT makes getting UCTT environments a bit easier to setup by expecting a few
configuration patterns.

### Expectations

1. It is expected that your project root will have either a conftest.py, a
uctt.py or a ucttc.py file in the root of your project.  This allows configuration
to be run in a manner that allows tools to be executed from subfolders.

2. It is expected that you will have a ./config folder as a main source of file
  based configuration.

  a. It is expected that you will provide a primary list of fixtures in a
     ./config/fixtures.yml|json file.
     You don't have to put all of your fixture config there, but at least tell
     UCTT what plugin type, plugin_id and instance_ids to use.
