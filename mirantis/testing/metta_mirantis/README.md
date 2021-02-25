# Mirantis common MEtta implementations

A metta contrib module that provides two main features:

1. A set of configuration options for including configuration to "test like we
  do".  These configuration "presets" allow easy injection of configuration that
  frees testers from having to discover tsting platforms, cluster sized and
  Mirantis product versions.

2. A set of terraform plans/root-modules that create infrastructure ideal for
  testing against.

## Usage

To use the presets, you need only do tow things:

1. Bootstrap your environment with `metta_mirantis_presets` which will tell
   metta to include code that users a project's `metta.yml` to indicate
   additional confiogutation that should be included.
2. Include a `metta.yml` file in your project config
