.. -*- coding: utf-8 -*-
   Copyright (C) 2024 CONTACT Software GmbH
   All rights reserved.
   https://www.contact-software.com/

.. _spin_python.behave:

==================
spin_python.behave
==================

The ``spin_python.behave`` plugin provides a way to run `behave`_ in the context
of cs.spin, which is a great tool for those who want to run acceptance tests
driven by behave.

How to setup the ``spin_python.behave`` plugin?
###############################################

To use the ``spin_python.behave`` plugin, a project's ``spinfile.yaml`` must at
least contain the following configuration.

.. code-block:: yaml
    :caption: Basic configuration of ``spinfile.yaml`` to leverage ``spin_python.behave``

    plugin_packages:
        - spin_python
    plugins:
        - spin_python.behave
    python:
        version: "3.11.9"

The provisioning of the required virtual environment as well as the plugins
dependencies can be done via the well-known ``spin provision``-task.

The plugin is now ready to use: ``spin behave --help``.

How to run tests against a CE16 instance using the pytest plugin?
#################################################################

Running tests against a CE16 instance requires this to exist. For the
creation of an instance, the ``spin_ce.mkinstance`` plugin can be used. To do
so, we have to define it within the project's ``spinfile.yaml`` (see
documentation of `spin_ce.mkinstance`_).

.. code-block:: yaml
    :caption: Excerpt of ``spinfile.yaml`` for testing against a CE16 instance

    plugin_packages:
        - spin_ce
        - spin_frontend
        - spin_java
        - spin_python
    plugins:
        - spin_ce.mkinstance
        - spin_python.behave
    ...

With a proper configuration and the mandatory provision, tests can be run by
executing the ``behave`` task. Here we explicitly define the DBMS backend to be
"sqlite" while passing the path to the created instance as an argument to the
``behave`` task.

.. code-block:: console
    :caption: Creation an instance and running tests against it

    spin provision
    spin -p mkinstance.dbms=sqlite mkinstance
    spin behave --instance sqlite

How to run the behave plugin in order to collect coverage?
##########################################################

Running tests and collecting coverage using the ``spin_python.behave`` plugin
can't be easier, since the plugin's default configuration already contains the
necessary flags and options to do so. For this reason, one just have to pass the
``-c`` or ``--coverage`` flag, to run tests and generate coverage reports.

.. code-block:: console

    spin behave --coverage

How to debug tests?
###################

Debugging tests executed by the behave plugin using `debugpy`_ can be achieved
by passing the ``--debug`` option when calling ``behave``. To diverge from the
default configuration used to run debugpy, one can adjust the ``{debugpy.opts}``.

.. code-block:: bash
    :caption: Debugging tests using the pytest plugin

    spin behave --debug -i sqlite

As soon as the debugpy server is listening, one can attach to it using the
desired IDE or debugger.

``spin_python.behave`` schema reference
#######################################

.. include:: behave_schemaref.rst
