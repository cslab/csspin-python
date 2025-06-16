.. -*- coding: utf-8 -*-
   Copyright (C) 2024 CONTACT Software GmbH
   https://www.contact-software.com/

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

.. _csspin_python.pytest:

====================
csspin_python.pytest
====================

The ``pytest`` plugin is a thin wrapper around the `pytest`_ package for testing
python-based projects. It makes use of `csspin`_'s configuration tree and thus
allows the usage of pre-defined settings while keeping the possibility to fully
adjust all options and flags passed to pytest.

How to setup the ``pytest`` plugin?
###################################

The configuration of the ``pytest`` plugin is as easy as those of
the ``python`` plugin.

.. code-block:: yaml
    :caption: Minimal configuration of ``spinfile.yaml`` to leverage ``pytest``

    plugin_packages:
        - csspin-python
    plugins:
        - csspin_python.pytest
    python:
        version: "3.11.9"

The provisioning of the required virtual environment as well as the plugins
dependencies can be done via the well-known ``spin provision``-task.

The plugin is now ready to use: ``spin pytest --help``.

How to run tests against a CE16 instance using the pytest plugin?
#################################################################

Running tests against a CE16 instance requires the existence those. For the
creation of an instance, the ``csspin_ce.mkinstance`` plugin can be used. To do
so, we have to define it within the project's ``spinfile.yaml`` (see
documentation of `csspin_ce.mkinstance`_).

.. code-block:: yaml
    :caption: Excerpt of ``spinfile.yaml`` for testing against a CE16 instance

    plugin_packages:
        - csspin-ce
        - csspin-python
    plugins:
        - csspin_ce.mkinstance
        - csspin_python.pytest
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

Running tests and collecting coverage using the ``pytest`` plugin
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

``pytest`` schema reference
###########################

.. include:: pytest_schemaref.rst
