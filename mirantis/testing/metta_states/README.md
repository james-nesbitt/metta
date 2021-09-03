# State based environments

This is an attempt to get state based environments integrated into Metta.

Metta environments aren't state based because metta tries hard to be declarative
which is kind of against multiple states.

## History

State integration was built into the second iteration of the environment, but
was factored out in the third generation.  The problem was that the integration
required deep integration that was both too complex for the simple case, and
not advanced enough for the interesting state usecases such as complex upgrades.

In the third iteration, environments were turned into plugins (and bootstrappers
were added) which allowed the complex state environment to be decoupled from the
simple cases, and were allowed to get their own complexity.

## Use Cases

The primary usecase for state based environments is the upgrade case.  This case
involved several sequential state changes. with each state being describable as
a set of fixtures which should be activated when the state is active.
The states for an upgrade test are usually sequential, but not stricly so as in
some scenarios you may be testing a downgrade.

## Typical components

### State plugins

A State plugin is an environment-like plugin which acts as a fixture container.
The plugin stays similar to an environment plugin in order to be usable by
consumers and plugins which are expecting environment plugins as parents, or
plugin containers.
The state plugin is then a container of fixtures and config which may be
activated or deactivated.

The state itself typically lives in an environment container.

@NOTE I am not certain that we actually need a state plugin. Perhaps just
  different types of environment plugins which act as states.

### State based Environment plugins

There is a state based environment plugin which acts as a container of state
plugins.  The environment should be able to "change state", which means to use
a different state container as its source of fixtures and config.
