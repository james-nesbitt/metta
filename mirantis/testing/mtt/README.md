# Mirantis Testing Toolbox (UCTT Extension)

The Mirantis testing toolbox is an extension of the UCTT clucter testing
toolbox.  

Extensions:
1. A UCTT provisioner plugin for launchpad
2. Some common config sources
3. A preset system to include configuration that Mirantis manages
4. A number of terraform plans/charts that we use.

## Usage

MTT has as a goal an easy to use injection into most testing paradigms.

First we offer a direct approach to creating the configerus objects that are
used heavily in UCTT.
Then we offer a pair of UCTT bootstrappers that allow inclusion of configerus
sources for config that we suggest for testing.
