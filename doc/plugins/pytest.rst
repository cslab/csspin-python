.. -*- coding: utf-8 -*-
   Copyright (C) 2024 CONTACT Software GmbH
   All rights reserved.
   https://www.contact-software.com/

.. _spin_python.pytest:

==================
spin_python.pytest
==================

The ``spin_python.pytest`` plugin is a thin wrapper around the `pytest`_ package for testing python-based
projects. It makes use of cs.spin's configuration tree and thus allows the usage
of pre-defined settings while keeping the possibility to fully adjust all
options and flags passed to pytest.

How to setup the ``spin_python.pytest`` plugin?
###############################################

The configuration of the ``spin_python.pytest`` plugin is as easy as those of
the ``spin_python.python`` plugin.

.. code-block:: yaml
    :caption: Minimal configuration of ``spinfile.yaml`` to leverage ``spin_python.pytest``

    plugin_packages:
        - spin_python
    plugins:
        - spin_python.pytest
    python:
        version: "3.11.9"

The provisioning of the required virtual environment as well as the plugins
dependencies can be done via the well-known ``spin provision``-task.

The plugin is now ready to use: ``spin pytest --help``.

How to run tests against a CE16 instance using the pytest plugin?
#################################################################

.. TODO: Add link to spin_ce.mkinstance documentation

Running tests against a CE16 instance requires the existence those. For the
creation of an instance, the ``spin_ce.mkinstance`` plugin can be used. To do
so, we have to define it within the project's ``spinfile.yaml`` (see
documentation of ``spin_ce.mkinstance``).

.. code-block:: yaml
    :caption: Excerpt of ``spinfile.yaml`` for testing against a CE16 instance

    plugin_packages:
        - spin_ce
        - spin_python
    plugins:
        - spin_ce.mkinstance
        - spin_python.pytest
    ...

With a proper configuration and the mandatory provision, tests can be run by
executing the ``pytest`` task. Here we explicitly define the DBMS backend to be
"sqlite" while passing the path to the created instance as an argument to the
``pytest`` task.

.. code-block:: console
    :caption: Creating an instance and running tests against it

    spin provision
    spin -p mkinstance.dbms=sqlite mkinstance
    spin pytest --instance sqlite

How to run the pytest plugin in order to collect coverage?
##########################################################

Running tests and collecting coverage using the ``spin_python.pytest`` plugin
can't be easier, since the plugin's default configuration already contains the
necessary flags and options to do so. For this reason, one just have to pass the
``-c`` or ``--coverage`` flag, to run tests and generate coverage reports.

.. code-block:: console

    spin provision
    spin pytest --coverage

How to debug tests?
###################

Debugging tests executed by the pytest plugin using `debugpy`_ can be achieved
by passing the ``--debug`` option when calling ``pytest``. To diverge from the
default configuration used to run debugpy, one can adjust the ``{debugpy.opts}``.

.. code-block:: bash
    :caption: Debugging tests using the pytest plugin

    spin pytest --debug

As soon as the debugpy server is listening, one can attach to it using the
desired IDE or debugger.

``spin_python.pytest`` schema reference
#######################################

.. include:: pytest_schemaref.rst
