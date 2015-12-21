============
Introduction
============


Requisites
----------

autopilot requires Python >= 3.5


Installation
------------

.. code-block:: bash

    pip install autopilot


Basic usage
-----------

Autopilot provides 2 commands, `new` and `release`. You can call them from the
command line::

    $ ap new
    $ ap release


`ap new` command creates a new project. You can pass optionally the new project
name::

    $ ap new cool-project


`ap release` creates a new release for a project. If you want to upload it to a
PyPI server, you need to create a configuration file to tell autopilot which
are your username and password. See next section for more info.


Configuration
-------------

We choose the yaml format for the configuration. This is the default
configuration file:


 .. literalinclude:: /../../src/autopilot/data/default_config.yml
        :language: yaml

For some options, if they are empty, autopilot will try to fill the data with
information from your system, see comments in the default configuration file.

It is possible to override the default configuration. To do it, create a file
at `XDG_CONFIG_HOME/autopilot/config.yml` (or `~/.config/autopilot/config.yml`
if `XDG_CONFIG_HOME` is not defined). You can override just some of the
options.  For every option, the logic is to look for the option in the user
configuration file, if it's not there, search in autopilot default
configuration, and if the option has an empty value, try to get the value from
the system.


An example of a custom configuration file:


.. code-block:: yaml

    new_project:
      license: mit

    editor: vim -R

    release:
      upload: nope
      push: false

    pypi_servers:

      pypi:
        user: my_pypi_user
        passeval: pass pypi

      local devpi:
        user: devpi_user
        passeval: pass devpi_local
        url: 'http://localhost:8080'


As you see, is possible to add more servers to `pypi_servers`. In this example,
a new PyPI server (`local devpi`) would be added to the list of options on the
UI.
