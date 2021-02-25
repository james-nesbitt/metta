# Metta_Mirantis Preset: Release

A mirantis metta preset that can select Mirantis product versions

This preset does nothing other than set some configuration.  You can then
leverage the included configuration in other config to produce impact.

## Usage

You need to do 2 things to include a release preset:

1. Bootstrap your environment with `metta_mirantis_presets` which will tell
   metta to look for presets in `metta.yml`
2. Include a `metta.yml` in your project which includes a which release you
   would like to include.

The `metta.yml` contents could be like:

metta.yml
```
presets:
    release: release/2021Q1
```
