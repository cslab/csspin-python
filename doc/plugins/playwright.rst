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

.. _csspin_python.playwright:

========================
csspin_python.playwright
========================

The ``playwright`` plugin provides a way to run the
`pytest-playwright`_ end-to-end testing tool to
execute pre-implemented tests against CONTACT Elements instances by adding the
``playwright`` task to spin's CLI.

How to setup the ``playwright`` plugin?
#######################################

For using the ``playwright`` plugin, a project's ``spinfile.yaml``
must at least contain the following configuration.

.. code-block:: yaml
    :caption: Minimal configuration of ``spinfile.yaml`` to leverage ``playwright``

    plugin_packages:
        - csspin-python
    plugins:
        - csspin_python.playwright
    python:
        version: "3.11.9"

The provisioning of the required virtual environment as well as the plugins
dependencies can be done via the well-known ``spin provision``-task.

The plugin is now ready to use: ``spin playwright --help``.

How to execute the ``playwright`` task?
#######################################

After provision, the ``playwright`` task can be executed as follows:

.. code-block:: bash
    :caption: Executing playwright

    spin playwright

The ``playwright`` task will execute the tests defined in the
``tests/playwright`` directory of the project. These path can be customized
using the playwright configuration within the ``spinfile.yaml``.

How to run playwright tests against a CONTACT Elements instance?
################################################################

Running playwright tests against a CONTACT Elements instance requires the
existence of it. A typical setup may require a
``spinfile.yaml`` as follows:

.. code-block:: yaml
    :caption: Configuration of ``spinfile.yaml`` to run playwright tests against a CONTACT Elements instance

    plugin_packages:
        - csspin-ce
        - csspin-frontend
        - csspin-java
        - csspin-python
    plugins:
        - csspin_ce:
            - mkinstance # for creating a CE instance
            - ce_services # for starting/stopping CE services
        - csspin_frontend.node
        - csspin_python.playwright
    python:
        version: '3.11.9'
        index_url: <index url where to retrieve cs.* packages from>
    node:
        version: '18.17.1'
    java:
        version: '21'

After provisioning the project, the CONTACT Elements instance can be created
and tested using the ``mkinstance`` and ``playwright`` tasks:

.. code-block:: bash
    :caption: Provisioning and running playwright tests against a CONTACT Elements instance

    spin provision
    spin mkinstance
    spin playwright

How to debug tests?
###################

Debugging tests executed by the playwright plugin using `debugpy`_ can be
achieved by passing the ``--debug`` option when calling ``playwright``. To
diverge from the default configuration used to run debugpy, one can adjust the
``{debugpy.opts}``.

.. code-block:: bash
    :caption: Debugging tests using the playwright plugin

    spin playwright --debug

As soon as the debugpy server is listening, one can attach to it using the
desired IDE or debugger.

``playwright`` schema reference
###############################

.. include:: playwright_schemaref.rst
