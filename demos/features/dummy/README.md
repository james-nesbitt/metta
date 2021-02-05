# Dummy plugins

The demo shows some general approaches for using the dummy plugins.

The dummy plugins are useful for two things:
1. showing how plugins work in general
2. dummy plugins can be dropped in for any other plugin for sfe injection and
   logging, when you aren't sure why your actual plugins are failing.

this demo shows the first, but you can use the config to swap out your plugins
as needed.

## The Demo

The demo uses pytest, to show how to use mtt with pytest, but mainly just to
get fast access to some executable code.

The demo does nothing but test some configuration and the demo plugins themselves.
It needs no additional resources, as it is more introspective than functional.

It is fast to run.

## To run it

Pre-requisites
1. install mtt using the standard instructions
2. install pytest as well using pip
3. run the code using `pytest`, perhaps with the `-s` flag.
